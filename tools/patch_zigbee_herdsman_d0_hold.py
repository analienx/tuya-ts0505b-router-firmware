#!/usr/bin/env python3
"""Fail-closed patcher for a D0 validation-only Zigbee OTA hold.

The patch changes the Zigbee OTA Upgrade End Response for exactly the frozen
TS0505B D0 tuple from the normal one-second activation delay to 0xFFFFFFFF
(wait for a later upgrade command). It does not start an OTA update.
"""
from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

MARKER = "TS0505B_D0_VALIDATION_HOLD"
D0_MANUFACTURER = "0x100b"
D0_IMAGE_TYPE = "0x020c"
D0_FILE_VERSION = "0x10003608"
NORMAL = "upgradeTime: 1,"
PATCHED = """upgradeTime:
                            // TS0505B_D0_VALIDATION_HOLD: hold only the frozen D0 tuple.
                            image.header.manufacturerCode === 0x100b && image.header.imageType === 0x020c && image.header.fileVersion === 0x10003608
                                ? 0xffffffff
                                : 1,"""
CONTEXT_TOKENS = (
    '"upgradeEndResponse"',
    "manufacturerCode: image.header.manufacturerCode",
    "imageType: image.header.imageType",
    "fileVersion: image.header.fileVersion",
    "currentTime: 0",
)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def find_normal_site(text: str) -> tuple[int, int]:
    positions: list[int] = []
    start = 0
    while True:
        pos = text.find(NORMAL, start)
        if pos < 0:
            break
        context = text[max(0, pos - 1600):pos]
        if all(token in context for token in CONTEXT_TOKENS):
            positions.append(pos)
        start = pos + len(NORMAL)
    if len(positions) != 1:
        raise ValueError(
            f"expected exactly one OTA activation site, found {len(positions)}"
        )
    return positions[0], positions[0] + len(NORMAL)
def state(text: str) -> str:
    marker_count = text.count(MARKER)
    if marker_count == 1:
        if all(value in text for value in (D0_MANUFACTURER, D0_IMAGE_TYPE, D0_FILE_VERSION)):
            return "PATCHED"
        raise ValueError("hold marker exists but frozen D0 tuple is incomplete")
    if marker_count > 1:
        raise ValueError(f"hold marker occurs {marker_count} times")
    find_normal_site(text)
    return "READY_TO_PATCH"


def apply_patch(path: Path) -> None:
    raw = path.read_bytes()
    text = raw.decode("utf-8")
    current = state(text)
    print(f"state={current} sha256={sha256(raw)}")
    if current == "PATCHED":
        print("already patched; no change")
        return

    begin, end = find_normal_site(text)
    patched = text[:begin] + PATCHED + text[end:]
    if state(patched) != "PATCHED":
        raise ValueError("post-patch self-check failed")
    backup = path.with_name(path.name + ".d0-hold.bak")
    if backup.exists():
        raise FileExistsError(f"refusing to overwrite existing backup: {backup}")
    backup.write_bytes(raw)
    path.write_text(patched, encoding="utf-8", newline="\n")
    print(f"backup={backup}")
    print(f"patched_sha256={sha256(path.read_bytes())}")


def revert_patch(path: Path) -> None:
    backup = path.with_name(path.name + ".d0-hold.bak")
    if not backup.exists():
        raise FileNotFoundError(f"backup not found: {backup}")
    current = path.read_text(encoding="utf-8")
    if state(current) != "PATCHED":
        raise ValueError("current file is not the expected D0 hold patch")
    original = backup.read_bytes()
    original_text = original.decode("utf-8")
    if state(original_text) != "READY_TO_PATCH":
        raise ValueError("backup is not an eligible unpatched herdsman file")
    path.write_bytes(original)
    backup.unlink()
    print(f"reverted_sha256={sha256(original)}")
def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("file", type=Path)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--apply", action="store_true")
    mode.add_argument("--revert", action="store_true")
    mode.add_argument("--require-patched", action="store_true")
    args = parser.parse_args()

    try:
        if args.apply:
            apply_patch(args.file)
        elif args.revert:
            revert_patch(args.file)
        else:
            raw = args.file.read_bytes()
            current = state(raw.decode("utf-8"))
            print(f"state={current} sha256={sha256(raw)}")
            if args.require_patched and current != "PATCHED":
                print("D0 validation hold is not installed")
                return 2
    except (OSError, UnicodeError, ValueError) as exc:
        print(f"D0 hold patch check FAILED: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
