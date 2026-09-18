#!/usr/bin/env python3
"""Validate exact live OTA identity and fail closed on unsafe deployment state."""
from __future__ import annotations

import json
import sys
from pathlib import Path

PATH = Path("firmware/target_manifest.json")
data = json.loads(PATH.read_text(encoding="utf-8"))
errors: list[str] = []

constraints = data["constraints"]
family = data["installed_family"]
ref = data["reference_platform"]
live = data["live_ota"]
corroboration = data["live_ota_corroboration"]
compat = data["compatibility"]
rollback = data["rollback"]
candidate = data["candidate"]
bootloader = data["bootloader_contract"]

LIVE_MANUFACTURER = 0x100B
LIVE_IMAGE_TYPE = 0x020C
LIVE_FILE_VERSION = 0x10003607

if data.get("schema_version") != 3:
    errors.append("target manifest schema must be 3")

if constraints["disassembly_allowed"] is not False:
    errors.append("disassembly must remain prohibited")
if constraints["swd_jtag_recovery_allowed"] is not False:
    errors.append("SWD/JTAG recovery must remain prohibited")
if constraints["deployment_transport"] != "zigbee_ota_only":
    errors.append("deployment transport must remain zigbee_ota_only")
if family["model_id"] != "TS0505B":
    errors.append("target model must remain TS0505B")
if family["manufacturer_name"] != "_TZ3210_mja6r5ix":
    errors.append("exact manufacturer target drifted")
if ref["module"] != "ZSU":
    errors.append("reference module must remain ZSU unless evidence review changes it")
if ref["ota_manufacturer_code"] != 0x1002 or ref["ota_image_type"] != 0x1602:
    errors.append("published Tuya reference identity must remain recorded as 0x1002/0x1602")

if live["checked"] is not True:
    errors.append("live OTA identity is now measured and must remain checked")
else:
    expected = (LIVE_MANUFACTURER, LIVE_IMAGE_TYPE, LIVE_FILE_VERSION)
    actual = (live["manufacturer_code"], live["image_type"], live["file_version"])
    if actual != expected:
        errors.append(
            "live OTA baseline drifted from measured 0x100B/0x020C/0x10003607; "
            "new device-originated evidence is required before changing it"
        )
    expected_match = (
        live["manufacturer_code"] == ref["ota_manufacturer_code"]
        and live["image_type"] == ref["ota_image_type"]
    )
    if live["matches_reference_identity"] is not expected_match:
        errors.append("matches_reference_identity does not match measured/reference tuples")
    if live.get("field_control") != 0:
        errors.append("measured live OTA field_control must remain 0")
    evidence = Path(live.get("evidence_source", ""))
    if not live.get("evidence_source") or not evidence.is_file():
        errors.append("live OTA evidence_source must point to committed evidence")
matching_peers = [
    item for item in corroboration
    if item.get("checked") is True
    and item.get("manufacturer_code") == live["manufacturer_code"]
    and item.get("image_type") == live["image_type"]
    and item.get("file_version") == live["file_version"]
]
if not matching_peers:
    errors.append("live OTA identity must retain at least one independently matching installed bulb")

if compat["live_ota_identity_authoritative_for_targeting"] is not True:
    errors.append("measured live OTA identity must be authoritative for candidate targeting")
if compat["generic_reference_identity_must_not_target_installed_population"] is not True:
    errors.append("generic 0x1002/0x1602 identity must remain prohibited for installed bulbs")
if live["manufacturer_code"] == ref["ota_manufacturer_code"] and live["image_type"] == ref["ota_image_type"]:
    errors.append("measured live identity unexpectedly collapsed to generic reference identity")

if bootloader.get("outer_ota_file_version_is_not_internal_app_version") is not True:
    errors.append("outer Zigbee OTA version must remain explicitly separate from GBL application version")
if bootloader.get("stock_application_properties_version_status") == "UNRESOLVED":
    if bootloader.get("stock_application_properties_version") is not None:
        errors.append("unresolved stock application-properties version must remain null")
else:
    if bootloader.get("stock_application_properties_version") is None:
        errors.append("resolved stock application-properties status requires a version")
boot_evidence = Path(bootloader.get("evidence_source", ""))
if not bootloader.get("evidence_source") or not boot_evidence.is_file():
    errors.append("bootloader contract evidence_source must point to committed evidence")

if data["deployment_ready"]:
    if compat["reference_binary_compatibility"] not in {"RECONCILED", "INDEPENDENTLY_PROVEN"}:
        errors.append("deployment_ready requires resolved platform/binary compatibility")
    if constraints["device_mutation_authorized"] is not True:
        errors.append("deployment_ready requires explicit mutation authorization")
    for key in ("source_sha", "app_sha256", "ug_gbl_sha256", "ota_sha256", "file_version"):
        if candidate.get(key) in (None, ""):
            errors.append(f"deployment_ready requires candidate.{key}")
    if candidate.get("ota_manufacturer_code") != live["manufacturer_code"]:
        errors.append("deployment_ready requires candidate manufacturer to match live 0x100B")
    if candidate.get("ota_image_type") != live["image_type"]:
        errors.append("deployment_ready requires candidate image type to match live 0x020C")
    if candidate.get("file_version") is not None and candidate["file_version"] <= live["file_version"]:
        errors.append("deployment_ready requires candidate OTA file version to advance live version")
    if rollback["status"] not in {"VERIFIED", "BOOTLOADER-REJECT-SAFE ONLY"}:
        errors.append("deployment_ready requires reviewed rollback classification")
    if bootloader.get("stock_application_properties_version_status") not in {"MEASURED", "INDEPENDENTLY_PROVEN", "RECONCILED"}:
        errors.append("deployment_ready requires resolved stock GBL application-properties version")
    for key in ("rollback_protection_policy", "upgrade_signature_policy", "upgrade_encryption_policy"):
        if bootloader.get(key) == "UNRESOLVED":
            errors.append(f"deployment_ready requires resolved bootloader {key}")
    if bootloader.get("candidate_acceptance_status") != "PROVEN_ACCEPTABLE":
        errors.append("deployment_ready requires proven bootloader acceptance status")
    for key in ("gbl_application_version", "gbl_signed", "gbl_encrypted"):
        if candidate.get(key) is None:
            errors.append(f"deployment_ready requires candidate.{key}")

if errors:
    print("Target manifest validation FAILED:")
    for error in errors:
        print(f" - {error}")
    sys.exit(1)

print("Target manifest validation PASS")
print(f" target={family['manufacturer_name']} / {family['model_id']}")
print(f" reference_ota=0x{ref['ota_manufacturer_code']:04X}/0x{ref['ota_image_type']:04X}")
print(
    f" live_ota=0x{live['manufacturer_code']:04X}/0x{live['image_type']:04X}/"
    f"0x{live['file_version']:08X} corroborated={len(matching_peers)}"
)
print(f" compatibility={compat['reference_binary_compatibility']} deployment_ready={data['deployment_ready']}")
