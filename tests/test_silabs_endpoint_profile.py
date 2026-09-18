import copy
import unittest

from tools.apply_silabs_endpoint_profile import apply_profile, validate_profile


def cluster(code, side, name=None, attributes=None):
    return {
        "name": name or f"cluster-{code}",
        "code": code,
        "mfgCode": None,
        "define": f"CLUSTER_{code}",
        "side": side,
        "enabled": 1,
        "attributes": attributes or [],
    }


def basic_cluster():
    return cluster(0, "server", "Basic", [
        {"name": "manufacturer name", "defaultValue": ""},
        {"name": "model identifier", "defaultValue": ""},
    ])


def source_doc():
    extended_clusters = [
        basic_cluster(),
        cluster(3, "server", "Identify"),
        cluster(4, "server", "Groups"),
        cluster(5, "server", "Scenes"),
        cluster(6, "server", "On/off"),
        cluster(8, "server", "Level Control"),
        cluster(0x0300, "server", "Color Control"),
        cluster(0x1000, "server", "ZLL Commissioning"),
        cluster(0x0019, "client", "Over the Air Bootloading"),
    ]
    return {
        "fileFormat": 2,
        "keyValuePairs": [{"key": "manufacturerCodes", "value": "0x1002"}],
        "endpointTypes": [
            {
                "id": 1, "name": "Centralized",
                "deviceTypeCode": 0x0101, "deviceTypeProfileId": 0x0104,
                "clusters": [basic_cluster(), cluster(6, "server")],
            },
            {
                "id": 2, "name": "Touchlink",
                "deviceTypeCode": 0x010D, "deviceTypeProfileId": 0x0104,
                "deviceTypeName": "LO-extendedcolorlight",
                "deviceTypeRef": {"code": 0x010D, "profileId": 0x0104},
                "deviceTypes": [{"code": 0x010D, "profileId": 0x0104}],
                "deviceVersions": [1], "deviceIdentifiers": [0x010D],
                "clusters": extended_clusters,
            },
            {
                "id": 3, "name": "GreenPower",
                "deviceTypeCode": 0x0061, "deviceTypeProfileId": 0xA1E0,
                "clusters": [cluster(0x0021, "client", "Green Power")],
            },
        ],
        "endpoints": [
            {"endpointTypeName": "Centralized", "endpointTypeIndex": 0,
             "profileId": 0x0104, "endpointId": 1, "networkId": 0},
            {"endpointTypeName": "Touchlink", "endpointTypeIndex": 1,
             "profileId": 0x0104, "endpointId": 2, "networkId": 0},
            {"endpointTypeName": "GreenPower", "endpointTypeIndex": 2,
             "profileId": 0xA1E0, "endpointId": 242, "networkId": 0},
        ],
    }


class EndpointProfileTests(unittest.TestCase):
    def test_profile_matches_live_endpoint_and_is_idempotent(self):
        first = apply_profile(source_doc())
        validate_profile(first)
        second = apply_profile(copy.deepcopy(first))
        self.assertEqual(first, second)

        self.assertEqual(first["endpoints"], [{
            "endpointTypeName": "HallBulbExtendedColorLight",
            "endpointTypeIndex": 0,
            "profileId": 0x0104,
            "endpointId": 1,
            "networkId": 0,
        }])
        target = first["endpointTypes"][0]
        self.assertEqual(target["deviceTypeCode"], 0x010D)
        self.assertEqual([c["code"] for c in target["clusters"] if c["side"] == "server"],
                         [0, 3, 4, 5, 6, 8, 0x0300, 0x1000])
        self.assertEqual([c["code"] for c in target["clusters"] if c["side"] == "client"],
                         [0x000A, 0x0019])
        basic = next(c for c in target["clusters"] if c["code"] == 0)
        attrs = {a["name"]: a.get("defaultValue") for a in basic["attributes"]}
        self.assertEqual(attrs["manufacturer name"], "_TZ3210_mja6r5ix")
        self.assertEqual(attrs["model identifier"], "TS0505B")
        self.assertEqual(
            [x["value"] for x in first["keyValuePairs"] if x["key"] == "manufacturerCodes"],
            ["0x100B"],
        )

    def test_missing_required_cluster_fails_closed(self):
        doc = source_doc()
        extended = next(et for et in doc["endpointTypes"] if et["deviceTypeCode"] == 0x010D)
        extended["clusters"] = [c for c in extended["clusters"] if c["code"] != 0x0300]
        with self.assertRaisesRegex(RuntimeError, "missing required clusters"):
            apply_profile(doc)

    def test_missing_basic_identity_attribute_fails_closed(self):
        doc = source_doc()
        extended = next(et for et in doc["endpointTypes"] if et["deviceTypeCode"] == 0x010D)
        basic = next(c for c in extended["clusters"] if c["code"] == 0)
        basic["attributes"] = [a for a in basic["attributes"]
                               if a["name"] != "manufacturer name"]
        with self.assertRaisesRegex(RuntimeError, "manufacturer name"):
            apply_profile(doc)


if __name__ == "__main__":
    unittest.main()
