import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXTENSION = ROOT / "integrations" / "zigbee2mqtt" / "d0_validation_hold_extension.mjs"


class Z2mD0AuthorizedOneShotTests(unittest.TestCase):
    def test_authorized_sidecar_publishes_once_and_blocks_replay(self):
        node = shutil.which("node")
        if node is None:
            self.skipTest("Node.js is required for the authorized one-shot runtime test")

        module_uri = EXTENSION.resolve().as_uri()
        with tempfile.TemporaryDirectory() as directory:
            script = Path(directory) / "one-shot-test.mjs"
            one_shot_dir = Path(directory) / "runtime"
            js = f"""
import assert from "node:assert/strict";
import crypto from "node:crypto";
import fs from "node:fs";

process.env.Z2M_D0_ONESHOT_DIR = {str(one_shot_dir)!r};
const mod = await import({module_uri!r} + "?one-shot-test");
const Hold = mod.default;

class Endpoint {{
    constructor(address) {{ this.deviceIeeeAddress = address; this.calls = []; }}
    async commandResponse(...args) {{ this.calls.push(args); return "ok"; }}
}}

const endpoint = new Endpoint("test-device");
const zigbee = {{zhController: {{*getDevicesIterator() {{ yield {{endpoints: [endpoint]}}; }}}}}};
const published = [];
const mqtt = {{publish: async (...args) => published.push(args)}};
const logs = [];
const logger = {{warning: (x) => logs.push(["warning", x]), error: (x) => logs.push(["error", x])}};

const image = Buffer.alloc(64);
image.writeUInt32LE(0x0beef11e, 0);
image.writeUInt16LE(0x100b, 10);
image.writeUInt16LE(0x020c, 12);
image.writeUInt32LE(0x10003608, 14);
image.writeUInt32LE(image.length, 52);
const digest = crypto.createHash("sha256").update(image).digest("hex");
const expected = {{
    target: "HallBulb2",
    topic: "zigbee2mqtt/bridge/request/device/ota_update/update",
    otaSha256: digest,
    otaSize: image.length,
    manufacturerCode: 0x100b,
    imageType: 0x020c,
    fileVersion: 0x10003608,
    fileName: "hallbulb-d0.1-noled.ota",
}};
fs.mkdirSync(process.env.Z2M_D0_ONESHOT_DIR, {{recursive: true}});
const pkg = {{
    mutation_authorized: true,
    authorization_scope: mod.AUTHORIZATION_SCOPE,
    topic: expected.topic,
    payload: {{
        id: expected.target,
        hex: {{data: image.toString("hex"), file_name: expected.fileName}},
    }},
    guard: {{
        validation_hold_required: true,
        manufacturer_code: expected.manufacturerCode,
        image_type: expected.imageType,
        file_version: expected.fileVersion,
        ota_sha256: expected.otaSha256,
    }},
}};
fs.writeFileSync(
    process.env.Z2M_D0_ONESHOT_DIR + "/HallBulb2-d0-validation-hold-AUTHORIZED.json",
    JSON.stringify(pkg),
);

const hold = new Hold(zigbee, mqtt, null, null, null, null, null, null, null, logger);
hold.expected = expected;
await hold.start();

const requestPublishes = published.filter((x) => x[0] === "bridge/request/device/ota_update/update");
assert.equal(requestPublishes.length, 1);
assert.deepEqual(requestPublishes[0][2], {{skipReceive: false}});
assert.equal(JSON.parse(requestPublishes[0][1]).id, "HallBulb2");

const sentinel = JSON.parse(
    fs.readFileSync(process.env.Z2M_D0_ONESHOT_DIR + "/HallBulb2-d0-validation-hold-FIRED.json", "utf8"),
);
assert.equal(sentinel.state, "published");
assert.equal(sentinel.ota_sha256, digest);
await hold.stop();
const second = new Hold(zigbee, mqtt, null, null, null, null, null, null, null, logger);
second.expected = expected;
await second.start();
const requestPublishesAfterRestart = published.filter((x) => x[0] === "bridge/request/device/ota_update/update");
assert.equal(requestPublishesAfterRestart.length, 1);
assert.equal(
    published.some((x) => x[0] === "bridge/d0_validation_hold_launch" && JSON.parse(x[1]).state === "blocked-replay"),
    true,
);
await second.stop();

const bad = structuredClone(pkg);
bad.guard.ota_sha256 = "0".repeat(64);
assert.throws(() => mod.validateAuthorizedPackage(bad, expected), /guard mismatch/);
"""
            script.write_text(js, encoding="utf-8")
            completed = subprocess.run(
                [node, str(script)],
                cwd=ROOT,
                capture_output=True,
                text=True,
                timeout=20,
            )

        self.assertEqual(
            completed.returncode,
            0,
            msg=f"Node authorized one-shot harness failed\nSTDOUT:\n{completed.stdout}\nSTDERR:\n{completed.stderr}",
        )


if __name__ == "__main__":
    unittest.main()
