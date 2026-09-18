#!/usr/bin/env python3
"""Validate that the generic Tuya/Silabs reference build stays non-deployable."""
from __future__ import annotations

import json
import sys
from pathlib import Path

PATH = Path("firmware/reference_build_manifest.json")
data = json.loads(PATH.read_text(encoding="utf-8"))
errors: list[str] = []

target = data["target"]
live = data["live_compatibility"]
toolchain = data["toolchain"]

if data.get("schema_version") != 2:
    errors.append("reference manifest schema must be 2")
if data.get("scope") != "STRUCTURAL_REFERENCE_ONLY":
    errors.append("reference build must remain structural/reference-only")
if target.get("ota_manufacturer_code") != 0x1002:
    errors.append("generic Tuya reference manufacturer must remain 0x1002")
if target.get("ota_image_type") != 0x1602:
    errors.append("generic Tuya reference image type must remain 0x1602")
if target.get("identity_scope") != "generic_tuya_reference_only":
    errors.append("reference identity scope drifted")
if target.get("deployable_to_installed_population") is not False:
    errors.append("generic reference must never be directly deployable")

expected_live = (0x100B, 0x020C, 0x10003607)
actual_live = (
    live.get("live_manufacturer_code"),
    live.get("live_image_type"),
    live.get("live_file_version"),
)
if live.get("live_tuple_checked") is not True or actual_live != expected_live:
    errors.append("reference manifest must retain measured live OTA baseline")
if live.get("identity_match") is not False:
    errors.append("generic reference/live identity mismatch must remain explicit")
if live.get("deployable") is not False:
    errors.append("reference build must remain non-deployable")

expected_toolchain = {
    "slt_version": "1.2.1-101",
    "simplicity_sdk": "2026.6.1",
    "zigbee_sdk": "9.1.1",
    "gcc_arm_none_eabi": "14.2.rel1",
}
for key, value in expected_toolchain.items():
    if toolchain.get(key) != value:
        errors.append(f"toolchain.{key} must remain pinned to {value}")

qio = data["artifacts"]["qio"]
ug = data["artifacts"]["ug"]
if qio.get("deployment_eligible") is not False:
    errors.append("QIO artifact must never be deployment-eligible")

if ug.get("ota_manufacturer_code") is not None:
    if ug["ota_manufacturer_code"] != target["ota_manufacturer_code"]:
        errors.append("reference UG manufacturer differs from reference target")
if ug.get("ota_image_type") is not None:
    if ug["ota_image_type"] != target["ota_image_type"]:
        errors.append("reference UG image type differs from reference target")

if errors:
    print("Reference manifest validation FAILED:")
    for error in errors:
        print(f" - {error}")
    sys.exit(1)

print("Reference manifest validation PASS")
print(
    f" reference=0x{target['ota_manufacturer_code']:04X}/"
    f"0x{target['ota_image_type']:04X} scope={data['scope']}"
)
print(
    f" live=0x{live['live_manufacturer_code']:04X}/"
    f"0x{live['live_image_type']:04X}/0x{live['live_file_version']:08X} "
    f"deployable={live['deployable']}"
)
