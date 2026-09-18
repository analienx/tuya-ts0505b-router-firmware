#!/usr/bin/env python3
"""Extract a device OTA Query Next Image tuple from Zigbee2MQTT debug logs.

This tool is intentionally offline/read-only: it parses an existing log and never
publishes MQTT messages or talks to a Zigbee device.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

REQUEST_RE = re.compile(
    r"Received Zigbee message from '(?P<device>[^']+)', type 'commandQueryNextImageRequest'.*?data '(?P<data>\{.*?\})' from endpoint"
)


def extract_tuples(text: str, device: str | None = None) -> list[dict]:
    found: list[dict] = []
    for line_number, line in enumerate(text.splitlines(), 1):
        match = REQUEST_RE.search(line)
        if not match:
            continue
        if device is not None and match.group("device") != device:
            continue
        payload = json.loads(match.group("data"))
        required = {"manufacturerCode", "imageType", "fileVersion"}
        if not required.issubset(payload):
            continue
        found.append(
            {
                "line": line_number,
                "device": match.group("device"),
                "field_control": payload.get("fieldControl"),
                "manufacturer_code": payload["manufacturerCode"],
                "manufacturer_code_hex": f"0x{payload['manufacturerCode']:04X}",
                "image_type": payload["imageType"],
                "image_type_hex": f"0x{payload['imageType']:04X}",
                "file_version": payload["fileVersion"],
                "file_version_hex": f"0x{payload['fileVersion']:08X}",
                "hardware_version": payload.get("hardwareVersion"),
            }
        )
    return found


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("log", type=Path)
    parser.add_argument("--device", default=None)
    parser.add_argument("--all", action="store_true", help="emit all matching requests, not just the latest")
    parser.add_argument("--expect-manufacturer", type=lambda x: int(x, 0), default=None)
    parser.add_argument("--expect-image-type", type=lambda x: int(x, 0), default=None)
    args = parser.parse_args()

    matches = extract_tuples(args.log.read_text(encoding="utf-8", errors="replace"), args.device)
    if not matches:
        raise SystemExit("no commandQueryNextImageRequest tuple found")

    output = matches if args.all else matches[-1]
    print(json.dumps(output, indent=2, sort_keys=True))

    latest = matches[-1]
    if args.expect_manufacturer is not None and latest["manufacturer_code"] != args.expect_manufacturer:
        raise SystemExit(
            f"manufacturer mismatch: {latest['manufacturer_code_hex']} != 0x{args.expect_manufacturer:04X}"
        )
    if args.expect_image_type is not None and latest["image_type"] != args.expect_image_type:
        raise SystemExit(f"image type mismatch: {latest['image_type_hex']} != 0x{args.expect_image_type:04X}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
