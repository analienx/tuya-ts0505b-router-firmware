#!/usr/bin/env python3
"""Inspect a candidate firmware artifact offline: hash, Zigbee OTA header and embedded GBL."""
from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path

try:
    from .parse_gbl import find_gbl, parse_gbl
    from .parse_zigbee_ota import OTA_MAGIC, parse_ota_header
except ImportError:  # direct script execution from tools/
    from parse_gbl import find_gbl, parse_gbl
    from parse_zigbee_ota import OTA_MAGIC, parse_ota_header


def inspect_artifact(blob: bytes) -> dict:
    result: dict = {
        "size": len(blob),
        "sha256": hashlib.sha256(blob).hexdigest(),
        "zigbee_ota": None,
        "gbl": None,
    }

    if len(blob) >= 4 and struct.unpack_from("<I", blob, 0)[0] == OTA_MAGIC:
        result["zigbee_ota"] = parse_ota_header(blob)

    gbl_offset = find_gbl(blob)
    if gbl_offset is not None:
        result["gbl"] = parse_gbl(blob, gbl_offset)

    if result["zigbee_ota"] is None and result["gbl"] is None:
        result["classification"] = "unknown_binary"
    elif result["zigbee_ota"] is not None and result["gbl"] is not None:
        result["classification"] = "zigbee_ota_with_embedded_gbl"
    elif result["zigbee_ota"] is not None:
        result["classification"] = "zigbee_ota"
    else:
        result["classification"] = "gbl"
    return result


def compare_target(result: dict, manifest: dict) -> dict:
    comparison = {
        "reference_manufacturer_matches": None,
        "reference_image_type_matches": None,
        "live_identity_matches": None,
        "candidate_version_advances_live": None,
        "manifest_deployment_ready": manifest.get("deployment_ready", False),
        "bootloader_stock_application_version_status": manifest.get("bootloader_contract", {}).get("stock_application_properties_version_status"),
        "gbl_application_version": None,
        "gbl_signed": None,
        "gbl_encrypted": None,
    }
    gbl = result.get("gbl")
    if gbl is not None:
        comparison["gbl_application_version"] = gbl.get("application_info", {}).get("application_version")
        comparison["gbl_signed"] = gbl.get("signed_flag")
        comparison["gbl_encrypted"] = gbl.get("encrypted_flag")

    ota = result.get("zigbee_ota")
    if ota is None:
        return comparison

    ref = manifest["reference_platform"]
    live = manifest["live_ota"]
    comparison["reference_manufacturer_matches"] = ota["manufacturer_code"] == ref["ota_manufacturer_code"]
    comparison["reference_image_type_matches"] = ota["image_type"] == ref["ota_image_type"]

    if live.get("checked"):
        comparison["live_identity_matches"] = (
            ota["manufacturer_code"] == live["manufacturer_code"]
            and ota["image_type"] == live["image_type"]
        )
        comparison["candidate_version_advances_live"] = ota["file_version"] > live["file_version"]
    return comparison


def target_match_errors(result: dict, manifest: dict) -> list[str]:
    """Return deployment-targeting errors; live identity wins once measured."""
    comparison = compare_target(result, manifest)
    live = manifest["live_ota"]
    errors: list[str] = []

    if result.get("zigbee_ota") is None:
        return ["artifact is not a Zigbee OTA container"]

    if live.get("checked"):
        if comparison["live_identity_matches"] is not True:
            errors.append("artifact does not match measured live OTA manufacturer/image type")
        if comparison["candidate_version_advances_live"] is not True:
            errors.append("artifact OTA file version does not advance measured live version")
    else:
        if comparison["reference_manufacturer_matches"] is not True:
            errors.append("artifact does not match fallback reference OTA manufacturer")
        if comparison["reference_image_type_matches"] is not True:
            errors.append("artifact does not match fallback reference OTA image type")
    return errors


def deployment_errors(result: dict, manifest: dict) -> list[str]:
    """Return fail-closed deployment errors beyond outer OTA target matching."""
    errors = target_match_errors(result, manifest)
    if manifest.get("deployment_ready") is not True:
        errors.append("target manifest deployment_ready is false")

    gbl = result.get("gbl")
    if gbl is None:
        errors.append("deployment requires an embedded GBL")
        return errors

    boot = manifest.get("bootloader_contract", {})
    if boot.get("stock_application_properties_version_status") not in {"MEASURED", "INDEPENDENTLY_PROVEN", "RECONCILED"}:
        errors.append("stock GBL application-properties version is unresolved")
    for key in ("rollback_protection_policy", "upgrade_signature_policy", "upgrade_encryption_policy"):
        if boot.get(key) == "UNRESOLVED":
            errors.append(f"bootloader {key} is unresolved")
    if boot.get("candidate_acceptance_status") != "PROVEN_ACCEPTABLE":
        errors.append("bootloader candidate acceptance is not proven")

    candidate = manifest.get("candidate", {})
    app_version = gbl.get("application_info", {}).get("application_version")
    expected_app_version = candidate.get("gbl_application_version")
    if expected_app_version is None:
        errors.append("candidate.gbl_application_version is unset")
    elif app_version != expected_app_version:
        errors.append("embedded GBL application version does not match candidate manifest")
    for field, actual in (("gbl_signed", gbl.get("signed_flag")), ("gbl_encrypted", gbl.get("encrypted_flag"))):
        expected = candidate.get(field)
        if expected is None:
            errors.append(f"candidate.{field} is unset")
        elif actual is not expected:
            errors.append(f"embedded {field} does not match candidate manifest")
    expected_ota_hash = candidate.get("ota_sha256")
    if not expected_ota_hash:
        errors.append("candidate.ota_sha256 is unset")
    elif result.get("sha256") != expected_ota_hash:
        errors.append("OTA SHA-256 does not match candidate manifest")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("file", type=Path)
    parser.add_argument("--manifest", type=Path, default=Path("firmware/target_manifest.json"))
    parser.add_argument("--require-target-match", action="store_true")
    parser.add_argument("--require-deployment-ready", action="store_true")
    args = parser.parse_args()

    result = inspect_artifact(args.file.read_bytes())
    manifest = None
    if args.manifest.exists():
        manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
        result["target_comparison"] = compare_target(result, manifest)

    print(json.dumps(result, indent=2, sort_keys=True))

    if args.require_target_match:
        if manifest is None:
            raise SystemExit("target manifest is required for --require-target-match")
        errors = target_match_errors(result, manifest)
        if errors:
            raise SystemExit("; ".join(errors))
    if args.require_deployment_ready:
        if manifest is None:
            raise SystemExit("target manifest is required for --require-deployment-ready")
        errors = deployment_errors(result, manifest)
        if errors:
            raise SystemExit("; ".join(errors))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
