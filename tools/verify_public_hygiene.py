#!/usr/bin/env python3
"""Fail closed if a public snapshot contains private identifiers, secrets, or deployable binaries."""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

REQUIRED = {"LICENSE", "SECURITY.md", "CONTRIBUTING.md", "THIRD_PARTY.md", "docs/FLASHABILITY.md"}
FORBIDDEN_SUFFIXES = {".ota", ".gbl", ".bin", ".hex", ".s37", ".elf"}
PATTERNS = {
    "private Zigbee IEEE": re.compile(r"0xa4c138[0-9a-f]{10}", re.I),
    "private key": re.compile(r"BEGIN (?:RSA |OPENSSH |EC |DSA )?PRIVATE KEY"),
    "GitHub token": re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}"),
    "Slack token": re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}"),
    "Google API key": re.compile(r"AIza[0-9A-Za-z_-]{30,}"),
    "Windows user path": re.compile(r"C:\\Users\\[^\\\s]+", re.I),
}

def tracked() -> list[Path]:
    raw = subprocess.check_output(["git", "ls-files", "-z"])
    return [Path(p.decode()) for p in raw.split(b"\0") if p]

def main() -> int:
    errors: list[str] = []
    paths = tracked()
    names = {p.as_posix() for p in paths}
    for req in REQUIRED:
        if req not in names:
            errors.append(f"required public file missing: {req}")
    for path in paths:
        if path.suffix.lower() in FORBIDDEN_SUFFIXES:
            errors.append(f"deployable/binary artifact must not be tracked: {path}")
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for label, pattern in PATTERNS.items():
            if pattern.search(text):
                errors.append(f"{label} found in {path}")
    if errors:
        print("Public hygiene validation FAILED:")
        for error in sorted(set(errors)):
            print(f" - {error}")
        return 1
    print(f"Public hygiene validation PASS ({len(paths)} tracked files)")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
