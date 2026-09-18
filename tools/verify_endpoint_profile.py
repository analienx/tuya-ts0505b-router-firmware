#!/usr/bin/env python3
import json
from pathlib import Path
import sys

PATH = Path("firmware/endpoint_profile.json")
data = json.loads(PATH.read_text(encoding="utf-8"))
errors = []


def require(condition, message):
    if not condition:
        errors.append(message)


require(data.get("schema_version") == 1, "endpoint profile schema must be 1")
require(data.get("endpoint_id") == 1, "installed light endpoint must be 1")
require(data.get("profile_id") == 0x0104, "profile must be Home Automation 0x0104")
require(data.get("device_type") == 0x010D, "device type must be Extended Color Light 0x010D")
require(data.get("device_type_hex") == "0x010D", "device type hex label drift")
require(data.get("server_clusters") == [0, 3, 4, 5, 6, 8, 0x0300, 0x1000],
        "server cluster list must match the live endpoint")
require(data.get("client_clusters") == [0x000A, 0x0019],
        "client cluster list must be Time + OTA")
require(data.get("zcl_manufacturer_code") == 0x100B,
        "ZCL manufacturer-code metadata must match live 0x100B")
require(data.get("manufacturer_name") == "_TZ3210_mja6r5ix",
        "Basic manufacturer name drift")
require(data.get("model_id") == "TS0505B", "Basic model identifier drift")
require(data.get("single_exposed_endpoint") is True,
        "endpoint profile must expose one application endpoint")
require(data.get("basic_identity_runtime_pending") is False,
        "Basic identity should be generated in ZAP")
require(data.get("ota_identity_runtime_pending") is True,
        "OTA image type/file version must remain unresolved")
require(data.get("physical_output_implementation") == "weak_noop",
        "physical output must remain inert")
require(data.get("deployment_eligible") is False,
        "endpoint profile must not be deployment eligible")
require(len(set(data.get("server_clusters", []))) == len(data.get("server_clusters", [])),
        "server clusters must be unique")
require(len(set(data.get("client_clusters", []))) == len(data.get("client_clusters", [])),
        "client clusters must be unique")
for forbidden in ("ota_image_type", "ota_file_version", "candidate_file_version"):
    require(forbidden not in data, f"endpoint profile must not define {forbidden}")

if errors:
    print("Endpoint profile validation FAILED:")
    for error in errors:
        print(f" - {error}")
    sys.exit(1)

print("Endpoint profile validation PASS")
print(" endpoint=1 profile=0x0104 device=0x010D server=8 client=2")
print(" Basic identity generated; OTA tuple still unresolved; deployment=false")
