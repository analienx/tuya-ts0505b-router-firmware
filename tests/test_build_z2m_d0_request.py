import hashlib
import unittest

from tools.build_z2m_d0_request import TOPIC, build_envelope


class BuildZ2mD0RequestTests(unittest.TestCase):
    def test_builds_prepared_only_single_device_envelope(self):
        blob = b"frozen-test-ota"
        spec = {
            "artifact": {
                "ota_size": len(blob),
                "ota_sha256": hashlib.sha256(blob).hexdigest(),
                "ota_filename": "d0.ota",
            },
            "ota_identity": {
                "manufacturer_code": 0x100B,
                "image_type": 0x020C,
                "file_version": 0x10003608,
            },
        }

        envelope = build_envelope("target-device", blob, spec)
        self.assertFalse(envelope["mutation_authorized"])
        self.assertEqual(envelope["topic"], TOPIC)
        self.assertEqual(envelope["payload"]["id"], "target-device")
        self.assertEqual(envelope["payload"]["hex"]["data"], blob.hex())
        self.assertEqual(envelope["payload"]["hex"]["file_name"], "d0.ota")
        self.assertTrue(envelope["guard"]["validation_hold_required"])

    def test_rejects_candidate_hash_drift(self):
        blob = b"candidate"
        spec = {
            "artifact": {"ota_size": len(blob), "ota_sha256": "0" * 64, "ota_filename": "d0.ota"},
            "ota_identity": {"manufacturer_code": 0x100B, "image_type": 0x020C, "file_version": 0x10003608},
        }
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            build_envelope("target-device", blob, spec)


if __name__ == "__main__":
    unittest.main()
