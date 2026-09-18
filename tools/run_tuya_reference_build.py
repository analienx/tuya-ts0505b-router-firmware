#!/usr/bin/env python3
"""Run a TuyaOS build locally and inventory generated artifacts.

This script performs build-only work. It never connects to Zigbee2MQTT, publishes
MQTT messages, flashes a device, or invokes production-programming tools.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

try:
    from .inspect_firmware_artifact import inspect_artifact
except ImportError:
    from inspect_firmware_artifact import inspect_artifact


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def candidate_files(output: Path) -> list[Path]:
    if not output.exists():
        return []
    files = []
    for path in output.rglob("*"):
        if not path.is_file():
            continue
        # Tuya platforms have used several filename conventions over time.
        # Inventory broadly; classify bytes instead of trusting extensions.
        if path.stat().st_size == 0:
            continue
        files.append(path)
    return sorted(files)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tuyaos-root", type=Path, required=True)
    parser.add_argument("--app-path", required=True, help="path passed to build_app.sh, e.g. apps/my_light")
    parser.add_argument("--app-name", required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--clean", action="store_true")
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()

    root = args.tuyaos_root.resolve()
    build_script = root / "build_app.sh"
    if not build_script.is_file():
        raise SystemExit(f"missing TuyaOS build entry point: {build_script}")

    app_dir = (root / args.app_path).resolve()
    if root not in app_dir.parents:
        raise SystemExit("app path must stay inside TuyaOS root")
    if not app_dir.is_dir():
        raise SystemExit(f"application directory not found: {app_dir}")

    commands: list[list[str]] = []
    if args.clean:
        commands.append(["sh", str(build_script), args.app_path, args.app_name, args.version, "clean"])
    commands.append(["sh", str(build_script), args.app_path, args.app_name, args.version])

    command_results = []
    for command in commands:
        proc = subprocess.run(
            command,
            cwd=root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
        command_results.append(
            {
                "command": command,
                "returncode": proc.returncode,
                "output_tail": proc.stdout.splitlines()[-200:],
            }
        )
        if proc.returncode != 0:
            report = {
                "status": "BUILD_FAILED",
                "commands": command_results,
                "artifacts": [],
            }
            args.report.parent.mkdir(parents=True, exist_ok=True)
            args.report.write_text(json.dumps(report, indent=2), encoding="utf-8")
            raise SystemExit(proc.returncode)

    output_dir = app_dir / "output"
    artifacts = []
    for path in candidate_files(output_dir):
        blob = path.read_bytes()
        try:
            inspection = inspect_artifact(blob)
        except Exception as exc:  # inventory must survive unsupported vendor files
            inspection = {"classification": "inspection_error", "error": str(exc)}
        artifacts.append(
            {
                "path": str(path.relative_to(root)),
                "size": path.stat().st_size,
                "sha256": sha256(path),
                "inspection": inspection,
            }
        )

    report = {
        "status": "BUILD_SUCCEEDED",
        "tuyaos_root": str(root),
        "app_path": args.app_path,
        "app_name": args.app_name,
        "version": args.version,
        "commands": command_results,
        "output_directory": str(output_dir),
        "artifacts": artifacts,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
