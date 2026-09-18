#!/usr/bin/env python3
"""Build, but never send, the frozen one-device D0 Zigbee2MQTT OTA request."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from pathlib import Path

MANIFEST = Path("firmware/canary_d0_manifest.json")
TOPIC = "zigbee2mqtt/bridge/request/device/ota_update/update"


def validate_candidate(blob: bytes, spec: dict) -> None:
    artifact = spec["artifact"]
    if len(blob) != artifact["ota_size"]:
        raise ValueError("OTA size differs from frozen D0 manifest")
    digest = hashlib.sha256(blob).hexdigest()
    if digest != artifact["ota_sha256"]:
        raise ValueError("OTA SHA-256 differs from frozen D0 manifest")


def build_envelope(device_id: str, blob: bytes, spec: dict) -> dict:
    if not device_id.strip():
        raise ValueError("device id must not be empty")
    validate_candidate(blob, spec)
    return {
        "mutation_authorized": False,
        "purpose": "prepared-only D0 validation-hold request; DO NOT publish without explicit authorization",
        "topic": TOPIC,
        "payload": {
            "id": device_id,
            "hex": {
                "data": blob.hex(),
                "file_name": spec["artifact"]["ota_filename"],
            },
            "image_block_request_timeout": 150000,
            "image_block_response_delay": 250,
            "default_maximum_data_size": 100,
        },
        "guard": {
            "manufacturer_code": spec["ota_identity"]["manufacturer_code"],
            "image_type": spec["ota_identity"]["image_type"],
            "file_version": spec["ota_identity"]["file_version"],
            "ota_sha256": spec["artifact"]["ota_sha256"],
            "validation_hold_required": True,
        },
    }


def write_atomic(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(data, handle, indent=2, sort_keys=True)
            handle.write("\n")
        os.replace(temporary, path)
    except Exception:
        Path(temporary).unlink(missing_ok=True)
        raise
def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("file", type=Path, help="frozen D0 .ota file")
    parser.add_argument("--id", required=True, help="single Zigbee2MQTT device id/friendly name")
    parser.add_argument("--output", type=Path, required=True, help="write prepared request envelope here")
    args = parser.parse_args()

    spec = json.loads(MANIFEST.read_text(encoding="utf-8"))
    envelope = build_envelope(args.id, args.file.read_bytes(), spec)
    write_atomic(args.output, envelope)

    print("Prepared D0 one-device request package")
    print(f" output={args.output}")
    print(f" topic={TOPIC}")
    print(f" id={args.id}")
    print(f" sha256={spec['artifact']['ota_sha256']}")
    print(" mutation_authorized=false; package was NOT published")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
