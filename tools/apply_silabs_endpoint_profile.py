#!/usr/bin/env python3
from __future__ import annotations

import argparse
from copy import deepcopy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROFILE_PATH = ROOT / "firmware" / "endpoint_profile.json"


def load_profile() -> dict:
    return json.loads(PROFILE_PATH.read_text(encoding="utf-8"))


def time_client_cluster() -> dict:
    return {
        "name": "Time",
        "code": 10,
        "mfgCode": None,
        "define": "TIME_CLUSTER",
        "side": "client",
        "enabled": 1,
        "attributes": [{
            "name": "cluster revision",
            "code": 65533,
            "mfgCode": None,
            "side": "client",
            "type": "int16u",
            "included": 1,
            "storageOption": "RAM",
            "singleton": 1,
            "bounded": 0,
            "defaultValue": "2",
            "reportable": 0,
            "minInterval": 1,
            "maxInterval": 65534,
            "reportableChange": 0,
        }],
    }


def _set_basic_identity(target: dict, profile: dict) -> None:
    basic = next((c for c in target.get("clusters", [])
                  if c.get("code") == 0 and c.get("side") == "server"), None)
    if basic is None:
        raise RuntimeError("Extended Color Light endpoint is missing Basic server cluster")
    attrs = {a.get("name"): a for a in basic.get("attributes", [])}
    required = {
        "manufacturer name": profile["manufacturer_name"],
        "model identifier": profile["model_id"],
    }
    for name, value in required.items():
        if name not in attrs:
            raise RuntimeError(f"Basic cluster missing {name!r}")
        attrs[name]["defaultValue"] = value


def apply_profile(doc: dict, profile: dict | None = None) -> dict:
    profile = profile or load_profile()
    candidates = [
        et for et in doc.get("endpointTypes", [])
        if et.get("deviceTypeCode") == profile["device_type"]
        and et.get("deviceTypeProfileId") == profile["profile_id"]
    ]
    if len(candidates) != 1:
        raise RuntimeError(
            f"expected one Extended Color Light endpoint type, found {len(candidates)}"
        )

    target = deepcopy(candidates[0])
    target["id"] = 1
    target["name"] = "HallBulbExtendedColorLight"
    wanted_server = profile["server_clusters"]
    wanted_client = profile["client_clusters"]
    cluster_map: dict[tuple[int, str], dict] = {}
    for cluster in target.get("clusters", []):
        key = (cluster.get("code"), cluster.get("side"))
        if cluster.get("enabled") != 1:
            continue
        if cluster.get("side") == "server" and cluster.get("code") in wanted_server:
            cluster_map[key] = deepcopy(cluster)
        elif cluster.get("side") == "client" and cluster.get("code") in wanted_client:
            cluster_map[key] = deepcopy(cluster)

    if (10, "client") not in cluster_map:
        cluster_map[(10, "client")] = time_client_cluster()

    missing = [
        (code, side)
        for side, codes in (("server", wanted_server), ("client", wanted_client))
        for code in codes
        if (code, side) not in cluster_map
    ]
    if missing:
        raise RuntimeError(f"source endpoint is missing required clusters: {missing}")

    target["clusters"] = (
        [cluster_map[(code, "server")] for code in wanted_server]
        + [cluster_map[(code, "client")] for code in wanted_client]
    )
    _set_basic_identity(target, profile)
    doc["endpointTypes"] = [target]
    doc["endpoints"] = [{
        "endpointTypeName": target["name"],
        "endpointTypeIndex": 0,
        "profileId": profile["profile_id"],
        "endpointId": profile["endpoint_id"],
        "networkId": 0,
    }]

    manufacturer_value = f"0x{profile['zcl_manufacturer_code']:04X}"
    for item in doc.setdefault("keyValuePairs", []):
        if item.get("key") == "manufacturerCodes":
            item["value"] = manufacturer_value
            break
    else:
        doc["keyValuePairs"].append({
            "key": "manufacturerCodes",
            "value": manufacturer_value,
        })

    validate_profile(doc, profile)
    return doc


def validate_profile(doc: dict, profile: dict | None = None) -> None:
    profile = profile or load_profile()
    if len(doc.get("endpointTypes", [])) != 1 or len(doc.get("endpoints", [])) != 1:
        raise RuntimeError("profile must expose exactly one endpoint type and one endpoint")

    target = doc["endpointTypes"][0]
    endpoint = doc["endpoints"][0]
    if endpoint.get("endpointId") != profile["endpoint_id"]:
        raise RuntimeError("endpoint id mismatch")
    if endpoint.get("profileId") != profile["profile_id"]:
        raise RuntimeError("HA profile mismatch")
    if target.get("deviceTypeCode") != profile["device_type"]:
        raise RuntimeError("device type mismatch")
    if target.get("deviceTypeProfileId") != profile["profile_id"]:
        raise RuntimeError("endpoint type profile mismatch")

    actual_server = [
        c["code"] for c in target.get("clusters", [])
        if c.get("enabled") == 1 and c.get("side") == "server"
    ]
    actual_client = [
        c["code"] for c in target.get("clusters", [])
        if c.get("enabled") == 1 and c.get("side") == "client"
    ]
    if actual_server != profile["server_clusters"]:
        raise RuntimeError(f"server cluster mismatch: {actual_server}")
    if actual_client != profile["client_clusters"]:
        raise RuntimeError(f"client cluster mismatch: {actual_client}")

    basic = next(c for c in target["clusters"]
                 if c.get("code") == 0 and c.get("side") == "server")
    attrs = {a.get("name"): a.get("defaultValue")
             for a in basic.get("attributes", [])}
    if attrs.get("manufacturer name") != profile["manufacturer_name"]:
        raise RuntimeError("Basic manufacturer name mismatch")
    if attrs.get("model identifier") != profile["model_id"]:
        raise RuntimeError("Basic model identifier mismatch")

    manufacturer_value = f"0x{profile['zcl_manufacturer_code']:04X}"
    codes = [item.get("value") for item in doc.get("keyValuePairs", [])
             if item.get("key") == "manufacturerCodes"]
    if codes != [manufacturer_value]:
        raise RuntimeError(f"ZCL manufacturer-code metadata mismatch: {codes}")


def transform_file(path: Path, output: Path | None = None) -> Path:
    doc = json.loads(path.read_text(encoding="utf-8"))
    transformed = apply_profile(doc)
    destination = output or path
    destination.write_text(json.dumps(transformed, indent=2) + "\n", encoding="utf-8")
    return destination


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Apply or validate the installed HallBulb endpoint profile in a ZAP file."
    )
    parser.add_argument("zap", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    if args.check:
        doc = json.loads(args.zap.read_text(encoding="utf-8"))
        validate_profile(doc)
        print(f"Endpoint profile validation PASS: {args.zap}")
        return 0

    destination = transform_file(args.zap, args.output)
    print(f"Applied HallBulb endpoint profile: {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
