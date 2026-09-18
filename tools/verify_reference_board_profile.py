#!/usr/bin/env python3
"""Validate that the Tuya board profile remains reference-only and fail-closed."""
from __future__ import annotations

import json
import sys
from pathlib import Path

PATH = Path("firmware/board_profiles/tuya_zsu_ts0505b_reference.json")
data = json.loads(PATH.read_text(encoding="utf-8"))
errors: list[str] = []

if data.get("schema_version") != 1:
    errors.append("reference board profile schema must be 1")
if data.get("status") != "REFERENCE_ONLY":
    errors.append("reference board profile must remain REFERENCE_ONLY")
if data.get("deployment_eligible") is not False:
    errors.append("reference board profile must remain non-deployable")
platform = data.get("platform", {})
if platform.get("module") != "ZSU":
    errors.append("reference module must remain ZSU")
if not str(platform.get("soc_primary", "")).startswith("EFR32MG21"):
    errors.append("reference primary SoC must remain MG21")
expected = {
    "red": "PA3",
    "green": "PD2",
    "blue": "PC5",
    "cold_white": "PA4",
    "warm_white": "PA0",
}
if data.get("channels") != expected:
    errors.append("Tuya published reference channel mapping drifted")
unknowns = set(data.get("electrical_unknowns", []))
for field in ("pwm_frequency", "pwm_polarity", "production_board_channel_mapping", "safe_reset_output_state"):
    if field not in unknowns:
        errors.append(f"required electrical unknown missing: {field}")
rules = data.get("rules", {})
if rules.get("custom_runtime_may_not_enable_outputs_from_this_profile") is not True:
    errors.append("reference profile must not authorize physical outputs")
if rules.get("requires_independent_production_board_evidence_before_deployment") is not True:
    errors.append("production board evidence requirement must remain enabled")

if errors:
    print("Reference board profile validation FAILED:")
    for error in errors:
        print(f" - {error}")
    sys.exit(1)

print("Reference board profile validation PASS")
print(" source=Tuya TS0505B/ZSU family reference; deployment=false")
print(" channels=R:PA3 G:PD2 B:PC5 CW:PA4 WW:PA0")
