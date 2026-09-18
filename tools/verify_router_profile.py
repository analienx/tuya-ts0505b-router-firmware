#!/usr/bin/env python3
"""Fail closed if the initial router policy drifts from its reviewed values."""
from pathlib import Path
import re
import sys

PROFILE = Path("firmware/router_profile.slcp.fragment.yaml")
text = PROFILE.read_text(encoding="utf-8")

expected = {
    "SL_ZIGBEE_NEIGHBOR_TABLE_SIZE": "26",
    "SL_ZIGBEE_ROUTE_TABLE_SIZE": "16",
    "SL_ZIGBEE_DISCOVERY_TABLE_SIZE": "8",
    "SL_ZIGBEE_ADDRESS_TABLE_SIZE": "12",
    "SL_ZIGBEE_BROADCAST_TABLE_SIZE": "15",
}

errors = []
for name, value in expected.items():
    pattern = rf"- name:\s*{re.escape(name)}\s*\n\s*value:\s*{re.escape(value)}(?:\s|$)"
    if not re.search(pattern, text):
        errors.append(f"{name} must be exactly {value}")

if "SLI_ZIGBEE_NETWORK_DEVICE_TYPE_ROUTER" not in text:
    errors.append("primary network device type must remain ROUTER")

for forbidden in (
    "router_as_concentrator",
    "periodic_many_to_one_originator",
    "guessed_gpio_mapping",
    "guessed_ota_identity",
):
    if forbidden not in text:
        errors.append(f"missing explicit forbidden design choice: {forbidden}")

if errors:
    print("Router profile validation FAILED:")
    for error in errors:
        print(f" - {error}")
    sys.exit(1)

print("Router profile validation PASS")
for name, value in expected.items():
    print(f" {name}={value}")
