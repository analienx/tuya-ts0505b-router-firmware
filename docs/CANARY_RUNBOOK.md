# One-device OTA canary runbook

This runbook is intentionally split at the first persistent mutation boundary. Everything before **F2** is read-only/build-only. The F2 section must not be executed until explicit user authorization is recorded in issue #1.

## Canary selection

Do not hard-code target-a as the eventual canary merely because it is the first device queried. Select between target-a and target-b only after fresh production metrics. target-c is explicitly ineligible as the first canary because its live OTA tuple was inferred rather than independently captured.

Installed candidates:

- target-a — `IEEE_REDACTED_A`
- target-b — `IEEE_REDACTED_B`
- target-c — `IEEE_REDACTED_C`

## A. Read-only OTA identity probe

Start with target-a for identity evidence.

Use Zigbee2MQTT's manual OTA **check** request only. The request must target exactly one device. Do not use the update/schedule endpoints.

Capture the Zigbee2MQTT debug log around the request. The decisive evidence is the device's `commandQueryNextImageRequest` payload containing:

- `manufacturerCode`
- `imageType`
- `fileVersion`
- `fieldControl`
- optional `hardwareVersion`

Save the log excerpt under `evidence/` and parse it with:

```sh
python tools/extract_ota_tuple_from_z2m_log.py <z2m-log> \
  --device target-a \
  --expect-manufacturer 0x100B \
  --expect-image-type 0x020C
```

These expected values are the measured installed-device identity. Any future mismatch requires new device-originated evidence; do not override it in an OTA index.

## B. Update target manifest from evidence

After parsing, update `firmware/target_manifest.json`:

- `live_ota.checked = true`
- exact decimal manufacturer code
- exact decimal image type
- exact `file_version`
- query status
- `matches_reference_identity` based on actual equality

Run:

```sh
python tools/verify_target_manifest.py
```

Keep `deployment_ready=false` and `device_mutation_authorized=false` throughout software bring-up.

## C. Build-only reference control

Build an **unmodified** Tuya TS0505B/ZSU reference target first using the pinned TuyaOS framework.

Example wrapper usage:

```sh
python tools/run_tuya_reference_build.py \
  --tuyaos-root <TUYAOS_ROOT> \
  --app-path apps/<APP> \
  --app-name <APP> \
  --version <REFERENCE_VERSION> \
  --clean \
  --report evidence/reference-build.json
```

The wrapper inventories all generated files and classifies Zigbee OTA / GBL structures offline. It never talks to a bulb.

## D. Candidate artifact inspection

For every UG/OTA candidate:

```sh
python tools/inspect_firmware_artifact.py <candidate> --require-target-match
```

Review:

- SHA-256
- Zigbee OTA manufacturer code
- image type
- file version
- total size
- optional hardware-version bounds
- embedded GBL version/type
- signed flag
- encrypted flag
- signature/certificate tags
- program-data flash addresses

The candidate must advance the live OTA file version according to the bootloader/client's comparison semantics. Never fake an incompatible manufacturer/image type just to force a transfer.

For the frozen D0 diagnostic candidate, run the stronger byte-for-byte gate against the actual local artifact:

```sh
python tools/preflight_d0_candidate.py <path-to-hallbulb-d0.1-noled.ota>
```

Before authorization this must report `D0 artifact preflight PASS` and `Mutation gate: CLOSED`. Running the same command with `--require-authorized` must fail until the deployment and authorization gates are deliberately opened.

## E. Pre-F2 candidate checklist

Before requesting permission for the first OTA update, all of these must be true or explicitly risk-classified:

- [ ] exact live OTA tuple captured twice consistently;
- [ ] generic-reference/live identity mismatch is reconciled or independently proven compatible;
- [ ] unmodified reference build succeeded;
- [ ] candidate build succeeded from recorded source SHA;
- [ ] router profile validator passes;
- [ ] target manifest validator passes;
- [ ] OTA parser reports exact live manufacturer/image type;
- [ ] file version is deliberate and newer than live version;
- [ ] GBL signed/encrypted state characterized;
- [ ] program ranges fit selected MG21 flash envelope;
- [ ] no concentrator / periodic many-to-one behavior;
- [ ] standard lighting behavior tests pass;
- [ ] known `_TZ3210_mja6r5ix` state/level desynchronization is covered by tests;
- [ ] rollback status classified honestly;
- [ ] exact canary selected after fresh health metrics;
- [ ] no OTA automation can target target-b/3 accidentally;
- [ ] candidate/index is restricted to one intended device/version path.

## F2 — first persistent OTA mutation

**STOP HERE until explicit user authorization.**

The actual Zigbee2MQTT OTA update request is a persistent production-device mutation. Immediately before it:

1. record direct user authorization in issue #1;
2. set the manifest authorization field only for the approved canary operation;
3. re-run all validators and artifact inspection;
4. capture fresh bulb reachability/LQI/stock version;
5. run `python tools/preflight_d0_candidate.py <candidate> --require-authorized` and require a zero exit status;
6. verify the OTA index/provider entry is restricted to the approved canary path and resolves to the exact frozen SHA-256;
7. issue exactly one canary update request;
8. observe transfer/verification/reboot continuously in the current session.

Do not retry blindly on failure and do not switch to another bulb as a diagnostic shortcut.

## G. Immediate postflight

After a successful candidate boot:

- confirm same IEEE and expected Zigbee identity;
- read Basic cluster/version;
- test Off → On → Off;
- brightness at low, moderate and high values;
- verify `onOff` and `currentLevel` match physical state;
- warm/mid/cool color temperature;
- R/G/B individually at low then moderate output;
- mixed transitions;
- complete off after every mode;
- Groups/Scenes if used in production;
- ordinary power cycle and rejoin;
- Zigbee2MQTT/coordinator restart recovery;
- capture reset/stack counters if exposed.

Immediate failure conditions:

- wrong color channel;
- full-power/stuck output;
- inability to turn off;
- flicker or thermal anomaly;
- reset loop;
- loss of OTA/Zigbee reachability;
- repeated leave/rejoin;
- network-wide route failure spike.

## H. Router soak

Minimum 24 h; preferred 72 h.

Compare against stock:

- ZCL timeout rate;
- median/p95 command latency;
- retries/failures where available;
- route/source-route error frequency;
- leave/rejoin/address-change events;
- neighbor and route-table occupancy/stability;
- evidence of useful forwarding when the mesh selects the bulb;
- reset/watchdog events;
- lighting correctness.

A higher LQI alone is not success.

## I. Expansion

If canary passes, update one additional bulb and observe before updating the third. Never perform a three-device simultaneous rollout for the first release.
