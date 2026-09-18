#!/usr/bin/env python3
"""Report the exact blockers between the current tree and an OTA-canary-ready release."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

MANIFEST = Path("firmware/target_manifest.json")
BUILD = Path("firmware/silabs_router_v0_build_manifest.json")

def blockers() -> list[str]:
    m = json.loads(MANIFEST.read_text(encoding="utf-8"))
    b = json.loads(BUILD.read_text(encoding="utf-8"))
    out: list[str] = []
    if m["compatibility"]["reference_binary_compatibility"] not in {"RECONCILED", "INDEPENDENTLY_PROVEN"}:
        out.append("installed platform/binary compatibility is not independently proven")
    if m["rollback"]["status"] not in {"VERIFIED", "BOOTLOADER-REJECT-SAFE ONLY"}:
        out.append("no verified OTA rollback or reviewed reject-safe recovery classification")
    boot = m["bootloader_contract"]
    if boot["stock_application_properties_version_status"] not in {"MEASURED", "INDEPENDENTLY_PROVEN", "RECONCILED"}:
        out.append("stock Gecko Application Properties version is unresolved")
    for key in ("rollback_protection_policy", "upgrade_signature_policy", "upgrade_encryption_policy"):
        if boot[key] == "UNRESOLVED":
            out.append(f"bootloader {key.replace('_', ' ')} is unresolved")
    if boot["candidate_acceptance_status"] != "PROVEN_ACCEPTABLE":
        out.append("bootloader acceptance of the candidate class is not proven")
    candidate = m["candidate"]
    for key in ("source_sha", "app_sha256", "ug_gbl_sha256", "ota_sha256", "file_version",
                "ota_manufacturer_code", "ota_image_type", "gbl_application_version",
                "gbl_signed", "gbl_encrypted"):
        if candidate.get(key) is None:
            out.append(f"candidate.{key} is not frozen")
    endpoint = b["endpoint_v0_build"]
    if endpoint.get("board_output_implementation") == "weak_noop":
        out.append("physical RGB+CCT board output profile is still inert/unverified")
    return out

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-ready", action="store_true")
    args = parser.parse_args()
    current = blockers()
    if current:
        print("Flashability gate: NOT READY")
        for item in current:
            print(f" - {item}")
        return 1 if args.require_ready else 0
    print("Flashability gate: READY FOR EXPLICITLY AUTHORIZED ONE-DEVICE CANARY")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
