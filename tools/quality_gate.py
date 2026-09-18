#!/usr/bin/env python3
"""Run the repository's deterministic software-quality gates."""
from __future__ import annotations

import argparse
import subprocess
import sys

STEPS = [
    [sys.executable, "tools/verify_router_profile.py"],
    [sys.executable, "tools/verify_target_manifest.py"],
    [sys.executable, "tools/verify_reference_manifest.py"],
    [sys.executable, "tools/verify_endpoint_profile.py"],
    [sys.executable, "tools/verify_silabs_router_build_manifest.py"],
    [sys.executable, "tools/verify_reference_board_profile.py"],
    [sys.executable, "tools/verify_canary_d0_manifest.py"],
    [sys.executable, "tools/verify_public_hygiene.py"],
    [sys.executable, "-m", "compileall", "-q", "tools", "tests"],
    [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
    [sys.executable, "tools/verify_flashability_gate.py"],
]

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-flashable", action="store_true")
    args = parser.parse_args()
    for command in STEPS:
        print("+", " ".join(command), flush=True)
        subprocess.run(command, check=True)
    if args.require_flashable:
        subprocess.run([sys.executable, "tools/verify_flashability_gate.py", "--require-ready"], check=True)
    print("QUALITY GATE PASS")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
