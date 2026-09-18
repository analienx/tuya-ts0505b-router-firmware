import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXTENSION = ROOT / "integrations" / "zigbee2mqtt" / "d0_validation_hold_extension.mjs"


class Z2mD0ValidationHoldExtensionTests(unittest.TestCase):
    def test_runtime_interception_and_restore(self):
        node = shutil.which("node")
        if node is None:
            self.skipTest("Node.js is required for the external-extension runtime test")

        module_uri = EXTENSION.resolve().as_uri()
        script = f"""
import assert from "node:assert/strict";
import Hold, {{matchesFrozenD0, HOLD_TIME}} from {module_uri!r};

class Endpoint {{
    constructor(address) {{
        this.deviceIeeeAddress = address;
        this.calls = [];
    }}

    async commandResponse(...args) {{
        this.calls.push(args);
        return "original-result";
    }}
}}

const endpoint = new Endpoint("test-device");
const original = Object.getPrototypeOf(endpoint).commandResponse;
const zigbee = {{
    zhController: {{
        *getDevicesIterator() {{
            yield {{endpoints: [endpoint]}};
        }},
    }},
}};
const published = [];
const warnings = [];
const mqtt = {{publish: async (...args) => published.push(args)}};
const logger = {{warning: (message) => warnings.push(message)}};

const hold = new Hold(zigbee, mqtt, null, null, null, null, null, null, null, logger);
await hold.start();

assert.equal(matchesFrozenD0("genOta", "upgradeEndResponse", {{
    manufacturerCode: 0x100b,
    imageType: 0x020c,
    fileVersion: 0x10003608,
}}), true);

const d0 = {{
    manufacturerCode: 0x100b,
    imageType: 0x020c,
    fileVersion: 0x10003608,
    currentTime: 0,
    upgradeTime: 1,
}};
const result = await endpoint.commandResponse("genOta", "upgradeEndResponse", d0, undefined, 9);
assert.equal(result, "original-result");
assert.equal(endpoint.calls.at(-1)[2].upgradeTime, HOLD_TIME);
assert.equal(d0.upgradeTime, 1);
assert.equal(warnings.length, 1);

const ordinary = {{manufacturerCode: 0x100b, imageType: 0x020c, fileVersion: 0x10003607, currentTime: 0, upgradeTime: 1}};
await endpoint.commandResponse("genOta", "upgradeEndResponse", ordinary, undefined, 10);
assert.equal(endpoint.calls.at(-1)[2].upgradeTime, 1);

await assert.rejects(
    endpoint.commandResponse("genOta", "upgradeEndResponse", {{...d0, upgradeTime: 2}}, undefined, 11),
    /refusing unexpected Upgrade End timing/,
);

assert.equal(JSON.parse(published[0][1]).active, true);
await hold.stop();
assert.equal(Object.getPrototypeOf(endpoint).commandResponse, original);
assert.equal(JSON.parse(published.at(-1)[1]).active, false);
"""
        with tempfile.TemporaryDirectory() as directory:
            harness = Path(directory) / "hold-test.mjs"
            harness.write_text(script, encoding="utf-8")
            completed = subprocess.run(
                [node, str(harness)],
                cwd=ROOT,
                capture_output=True,
                text=True,
                timeout=20,
            )

        self.assertEqual(
            completed.returncode,
            0,
            msg=f"Node extension harness failed\nSTDOUT:\n{completed.stdout}\nSTDERR:\n{completed.stderr}",
        )


if __name__ == "__main__":
    unittest.main()
