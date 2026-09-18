#!/usr/bin/env python3
"""Offline byte-for-byte preflight for the frozen D0 diagnostic OTA."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

try:
    from .inspect_firmware_artifact import inspect_artifact
    from .parse_gbl import find_gbl
except ImportError:
    from inspect_firmware_artifact import inspect_artifact
    from parse_gbl import find_gbl

CANARY = Path("firmware/canary_d0_manifest.json")
TARGET = Path("firmware/target_manifest.json")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("file", type=Path)
    parser.add_argument("--require-authorized", action="store_true")
    args = parser.parse_args()

    spec = json.loads(CANARY.read_text(encoding="utf-8"))
    target = json.loads(TARGET.read_text(encoding="utf-8"))
    blob = args.file.read_bytes()
    result = inspect_artifact(blob)
    errors: list[str] = []
    artifact = spec["artifact"]
    if len(blob) != artifact["ota_size"]:
        errors.append("OTA size differs from frozen D0")
    if hashlib.sha256(blob).hexdigest() != artifact["ota_sha256"]:
        errors.append("OTA SHA-256 differs from frozen D0")

    ota = result.get("zigbee_ota")
    expected_ota = spec["ota_identity"]
    if ota is None:
        errors.append("candidate is not a Zigbee OTA container")
    else:
        for field in ("manufacturer_code", "image_type", "file_version", "stack_version", "header_string"):
            if ota.get(field) != expected_ota[field]:
                errors.append(f"OTA {field} differs from frozen D0")
        if ota.get("declared_size_matches_file") is not True:
            errors.append("OTA declared size does not match file")

    offset = find_gbl(blob)
    if offset is None:
        errors.append("embedded GBL header not found")
    else:
        gbl_blob = blob[offset:]
        if len(gbl_blob) != artifact["gbl_size"]:
            errors.append("embedded GBL size differs from frozen D0")
        if hashlib.sha256(gbl_blob).hexdigest() != artifact["gbl_sha256"]:
            errors.append("embedded GBL SHA-256 differs from frozen D0")
    gbl = result.get("gbl")
    if gbl is None:
        errors.append("GBL parse failed")
    else:
        expected_gbl = spec["gbl"]
        app = gbl.get("application_info") or {}
        if app.get("application_version") != expected_gbl["application_version"]:
            errors.append("GBL application version differs from frozen D0")
        if gbl.get("signed_flag") is not expected_gbl["signed"]:
            errors.append("GBL signed state differs from frozen D0")
        if gbl.get("encrypted_flag") is not expected_gbl["encrypted"]:
            errors.append("GBL encrypted state differs from frozen D0")
        if gbl.get("has_bootloader_upgrade") is not False:
            errors.append("GBL unexpectedly contains bootloader upgrade data")
        if gbl.get("has_se_upgrade") is not False:
            errors.append("GBL unexpectedly contains SE upgrade data")

        sequence = [tag["name"] for tag in gbl.get("tags", [])]
        if sequence != expected_gbl["tag_sequence"]:
            errors.append("GBL tag sequence differs from frozen D0")
        ranges = []
        for item in gbl.get("program_ranges", []):
            if item.get("encoding") != "plain":
                errors.append("D0 contains a non-plain program range")
                continue
            ranges.append((
                item["flash_start_address_hex"],
                item.get("flash_end_address_exclusive_hex"),
                item.get("flash_data_length"),
            ))
        expected_ranges = [
            (x["start_hex"], x["end_exclusive_hex"], x["length"])
            for x in spec["program_ranges"]
        ]
        if ranges != expected_ranges:
            errors.append("GBL program ranges differ from independently verified D0 ranges")

    live = target["live_ota"]
    if (expected_ota["manufacturer_code"], expected_ota["image_type"]) != (
        live["manufacturer_code"], live["image_type"]
    ):
        errors.append("frozen D0 no longer matches measured live target identity")
    if expected_ota["file_version"] <= live["file_version"]:
        errors.append("frozen D0 no longer advances live OTA version")
    if errors:
        print("D0 artifact preflight FAILED:")
        for error in errors:
            print(f" - {error}")
        return 1

    print("D0 artifact preflight PASS")
    print(f" sha256={artifact['ota_sha256']}")
    print(" ranges=0x4000..0x4234, 0x4238..0x4E548")
    print(" bootloader/SE payloads=absent; signed=false; encrypted=false")

    gate_errors: list[str] = []
    if target.get("deployment_ready") is not True:
        gate_errors.append("target manifest deployment_ready is false")
    if target["constraints"].get("device_mutation_authorized") is not True:
        gate_errors.append("explicit device mutation authorization is not recorded")
    if spec.get("deployment_ready") is not True:
        gate_errors.append("D0 canary manifest deployment_ready is false")

    if gate_errors:
        print("Mutation gate: CLOSED")
        for error in gate_errors:
            print(f" - {error}")
        return 1 if args.require_authorized else 0

    print("Mutation gate: OPEN for the explicitly authorized one-device canary")
    return 0


if __name__ == "__main__":
    sys.exit(main())
