import struct
import unittest

from tools.inspect_firmware_artifact import (
    compare_target, deployment_errors, inspect_artifact, target_match_errors,
)
from tools.parse_zigbee_ota import OTA_MAGIC


class InspectFirmwareArtifactTests(unittest.TestCase):
    def make_ota(self, manufacturer=0x1002, image_type=0x1602, file_version=0x71):
        body = b"PAYLOAD"
        header_length = 56
        total = header_length + len(body)
        header = struct.pack(
            "<IHHHHHIH",
            OTA_MAGIC,
            0x0100,
            header_length,
            0,
            manufacturer,
            image_type,
            file_version,
            2,
        )
        header += b"TS0505B-router-test".ljust(32, b"\x00")
        header += struct.pack("<I", total)
        return header + body

    def manifest(self, checked=False):
        return {
            "deployment_ready": False,
            "reference_platform": {
                "ota_manufacturer_code": 0x1002,
                "ota_image_type": 0x1602,
            },
            "live_ota": {
                "checked": checked,
                "manufacturer_code": 0x100B if checked else None,
                "image_type": 0x020C if checked else None,
                "file_version": 0x10003607 if checked else None,
            },
            "bootloader_contract": {
                "stock_application_properties_version_status": "UNRESOLVED",
                "rollback_protection_policy": "UNRESOLVED",
                "upgrade_signature_policy": "UNRESOLVED",
                "upgrade_encryption_policy": "UNRESOLVED",
                "candidate_acceptance_status": "UNRESOLVED",
            },
            "candidate": {
                "gbl_application_version": None,
                "gbl_signed": None,
                "gbl_encrypted": None,
                "ota_sha256": None,
            },
        }

    def test_classifies_zigbee_ota(self):
        result = inspect_artifact(self.make_ota())
        self.assertEqual(result["classification"], "zigbee_ota")
        self.assertIsNotNone(result["sha256"])
        self.assertEqual(result["zigbee_ota"]["manufacturer_code"], 0x1002)

    def test_reference_comparison_before_live_probe(self):
        result = inspect_artifact(self.make_ota())
        comparison = compare_target(result, self.manifest())
        self.assertTrue(comparison["reference_manufacturer_matches"])
        self.assertTrue(comparison["reference_image_type_matches"])
        self.assertIsNone(comparison["live_identity_matches"])

    def test_live_candidate_can_differ_from_reference(self):
        result = inspect_artifact(self.make_ota(
            manufacturer=0x100B, image_type=0x020C, file_version=0x10003608
        ))
        comparison = compare_target(result, self.manifest(checked=True))
        self.assertFalse(comparison["reference_manufacturer_matches"])
        self.assertFalse(comparison["reference_image_type_matches"])
        self.assertTrue(comparison["live_identity_matches"])
        self.assertTrue(comparison["candidate_version_advances_live"])
        self.assertEqual(target_match_errors(result, self.manifest(checked=True)), [])

    def test_generic_reference_identity_is_rejected_after_live_probe(self):
        result = inspect_artifact(self.make_ota(file_version=0x10003608))
        errors = target_match_errors(result, self.manifest(checked=True))
        self.assertIn("artifact does not match measured live OTA manufacturer/image type", errors)

    def test_live_version_must_advance(self):
        result = inspect_artifact(self.make_ota(
            manufacturer=0x100B, image_type=0x020C, file_version=0x10003607
        ))
        errors = target_match_errors(result, self.manifest(checked=True))
        self.assertIn("artifact OTA file version does not advance measured live version", errors)

    def test_deployment_gate_fails_closed_when_manifest_is_not_ready(self):
        result = inspect_artifact(self.make_ota(
            manufacturer=0x100B, image_type=0x020C, file_version=0x10003608
        ))
        errors = deployment_errors(result, self.manifest(checked=True))
        self.assertIn("target manifest deployment_ready is false", errors)
        self.assertIn("deployment requires an embedded GBL", errors)

    def test_deployment_gate_rejects_embedded_gbl_with_unresolved_bootloader_contract(self):
        result = inspect_artifact(self.make_ota(
            manufacturer=0x100B, image_type=0x020C, file_version=0x10003608
        ))
        result["gbl"] = {
            "application_info": {"application_version": 1},
            "signed_flag": False,
            "encrypted_flag": False,
        }
        errors = deployment_errors(result, self.manifest(checked=True))
        self.assertIn("stock GBL application-properties version is unresolved", errors)
        self.assertIn("bootloader rollback_protection_policy is unresolved", errors)
        self.assertIn("bootloader upgrade_signature_policy is unresolved", errors)
        self.assertIn("bootloader upgrade_encryption_policy is unresolved", errors)
        self.assertIn("bootloader candidate acceptance is not proven", errors)
        self.assertIn("candidate.gbl_application_version is unset", errors)

    def test_unknown_binary(self):
        result = inspect_artifact(b"not-a-firmware-container")
        self.assertEqual(result["classification"], "unknown_binary")


if __name__ == "__main__":
    unittest.main()
