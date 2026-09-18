import tempfile
import unittest
from pathlib import Path

from tools.patch_zigbee_herdsman_d0_hold import (
    MARKER,
    apply_patch,
    revert_patch,
    state,
)

FIXTURE = """
await endpoint.commandResponse(
    "genOta",
    "upgradeEndResponse",
    {
        manufacturerCode: image.header.manufacturerCode,
        imageType: image.header.imageType,
        fileVersion: image.header.fileVersion,
        // using 0 tells the device to use upgradeTime as offset
        currentTime: 0,
        upgradeTime: 1,
    },
);
"""
class D0HoldPatchTests(unittest.TestCase):
    def test_ready_apply_and_revert(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "device.ts"
            path.write_text(FIXTURE, encoding="utf-8")

            self.assertEqual(state(path.read_text(encoding="utf-8")), "READY_TO_PATCH")
            apply_patch(path)

            patched = path.read_text(encoding="utf-8")
            self.assertEqual(state(patched), "PATCHED")
            self.assertEqual(patched.count(MARKER), 1)
            self.assertIn("0x100b", patched)
            self.assertIn("0x020c", patched)
            self.assertIn("0x10003608", patched)
            self.assertIn("? 0xffffffff", patched)
            self.assertTrue(path.with_name("device.ts.d0-hold.bak").exists())

            revert_patch(path)
            self.assertEqual(path.read_text(encoding="utf-8"), FIXTURE)
            self.assertFalse(path.with_name("device.ts.d0-hold.bak").exists())
    def test_refuses_ambiguous_activation_sites(self):
        with self.assertRaises(ValueError):
            state(FIXTURE + "\n" + FIXTURE)

    def test_refuses_unrelated_upgrade_time(self):
        text = """
const x = {
    currentTime: 0,
    upgradeTime: 1,
};
"""
        with self.assertRaises(ValueError):
            state(text)


if __name__ == "__main__":
    unittest.main()
