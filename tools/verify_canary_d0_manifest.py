#!/usr/bin/env python3
"""Validate the frozen D0 canary metadata without requiring firmware binaries."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

PATH = Path("firmware/canary_d0_manifest.json")
TARGET = Path("firmware/target_manifest.json")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def main() -> int:
    data = json.loads(PATH.read_text(encoding="utf-8"))
    target = json.loads(TARGET.read_text(encoding="utf-8"))
    errors: list[str] = []

    if data.get("schema_version") != 1:
        errors.append("canary manifest schema must be 1")
    if data.get("candidate") != "d0.1-noled":
        errors.append("unexpected D0 candidate name")
    if data.get("deployment_ready") is not False:
        errors.append("public D0 manifest must remain non-deployable")

    artifact = data["artifact"]
    for key in ("ota_sha256", "gbl_sha256", "app_sha256"):
        if not SHA256_RE.fullmatch(artifact.get(key, "")):
            errors.append(f"artifact.{key} must be lowercase SHA-256")
    identity = data["ota_identity"]
    live = target["live_ota"]
    if identity["manufacturer_code"] != live["manufacturer_code"]:
        errors.append("D0 manufacturer does not match live target")
    if identity["image_type"] != live["image_type"]:
        errors.append("D0 image type does not match live target")
    if identity["file_version"] <= live["file_version"]:
        errors.append("D0 OTA version must advance live version")

    gbl = data["gbl"]
    if gbl["bootloader_upgrade_payload"] is not False:
        errors.append("D0 must not contain a bootloader upgrade payload")
    if gbl["se_upgrade_payload"] is not False:
        errors.append("D0 must not contain an SE upgrade payload")
    if gbl["signed"] is not False or gbl["encrypted"] is not False:
        errors.append("frozen D0 security flags drifted")

    ranges = data["program_ranges"]
    expected = [
        ("0x00004000", "0x00004234", 564),
        ("0x00004238", "0x0004E548", 303888),
    ]
    actual = [(x["start_hex"], x["end_exclusive_hex"], x["length"]) for x in ranges]
    if actual != expected:
        errors.append("D0 verified program ranges drifted")
    env = data["erase_envelope"]
    if int(env["highest_erased_page_end_hex"], 0) > int(env["conservative_768k_flash_end_hex"], 0):
        errors.append("D0 erase envelope exceeds conservative flash ceiling")
    if data["verification"]["status"] != "PASS_FLASH_LAYOUT_ONLY":
        errors.append("D0 verification status must remain PASS_FLASH_LAYOUT_ONLY")
    if not data.get("remaining_stop_conditions"):
        errors.append("D0 must retain explicit stop conditions")

    if errors:
        print("D0 canary manifest validation FAILED:")
        for error in errors:
            print(f" - {error}")
        return 1

    print("D0 canary manifest validation PASS")
    print(
        f" ota=0x{identity['manufacturer_code']:04X}/"
        f"0x{identity['image_type']:04X}/0x{identity['file_version']:08X}"
    )
    print(f" sha256={artifact['ota_sha256']}")
    print(" deployment_ready=false; explicit mutation gate remains closed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
