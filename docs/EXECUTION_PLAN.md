# Full execution plan — TS0505B better-router firmware

This plan converts the project from research into an evidence-gated OTA-first implementation. It assumes the installed `_TZ3210_mja6r5ix` bulbs cannot be disassembled and therefore excludes SWD/JTAG/open-bulb recovery.

## Objective

Produce a reproducible custom firmware candidate for the three installed Tuya `TS0505B_1_1` RGB+CCT bulbs that:

- preserves correct Zigbee lighting behavior;
- preserves or improves Tuya/Zigbee2MQTT interoperability;
- materially improves router reliability in the production mesh;
- can be delivered through Zigbee OTA without physical access;
- is first validated on exactly one canary.

The stock bulbs are already routers. The project goal is a **better implementation of the router/application**, not a logical-type conversion.

---

## Phase 0 — freeze constraints and success criteria

### Tasks

- Treat `target-a..3` as production devices.
- No disassembly, debug-pad access or physical firmware recovery.
- No OTA install/update/schedule until explicit F2 authorization.
- Preserve one-canary-first policy.
- Define stock failure baseline from existing 10 s command timeouts.

### Exit criteria

- Repository documents no-disassembly constraint.
- Router policy and application compatibility goals are machine-checkable where possible.
- First-write boundary is unambiguous.

---

## Phase 1 — live read-only identity capture

### 1.1 Basic/device identity

For all three bulbs capture:

- IEEE address;
- network address;
- manufacturer/model;
- app version / stack version / hardware version / software build ID;
- power source and node descriptor;
- endpoint 1 descriptor and in/out clusters;
- logical type/router MAC capabilities.

### 1.2 OTA tuple

Run Zigbee2MQTT manual OTA `check` for `target-a` only initially. Record:

- manufacturer code;
- image type;
- current installed file version;
- whether Query Next Image completes;
- response/status/error;
- whether the device advertises any constraints such as hardware version;
- whether Zigbee2MQTT sees a matching public image.

This action must remain a **check**, never `update`, `schedule` or downgrade.

### 1.3 Routing/network baseline

Capture at least:

- current LQI distribution over several observations;
- command success/failure and latency;
- leave/rejoin count;
- network address changes;
- route/source-route errors involving the bulbs;
- management LQI support;
- management routing-table support;
- available neighbor/route evidence;
- coordinator restart and ordinary power-cycle recovery behavior already visible in logs.

### Exit criteria

A machine-readable evidence file identifies the exact live OTA tuple and the production baseline.

---

## Phase 2 — prove compatible platform envelope

### Evidence state

Tuya's published TS0505B Lighting Product Development Kit remains strong family/reference evidence for ZSU/EFR32MG21, router role, Extended Color Light/RGBCW behavior, and generic OTA identity `0x1002/0x1602`.

Live production evidence now overrides that tuple for OTA targeting. target-a and target-b independently emitted `manufacturerCode=0x100B`, `imageType=0x020C`, `fileVersion=0x10003607`, `fieldControl=0`.

### Decision

The generic Tuya build must **not** be promoted directly to the installed-device binary compatibility envelope. Continue software-only investigation of the OEM identity difference. A build-only Tuya reference remains useful for structure, lighting behavior, flash layout, GBL/UG packaging and router integration research, but any deployable candidate must use the measured live manufacturer/image identity and must have independently reconciled bootloader/platform compatibility.

### Flash geometry

Keep the 768 KiB documented alternative as the conservative flash envelope until software/build evidence proves the installed population can safely assume the 1024 KiB ZSU target. Do not infer flash geometry from the OTA tuple alone.

### Exit criteria

- OEM/reference OTA identity difference explained or independently proven compatible;
- selected compile target documented;
- maximum safe application/storage assumptions documented;
- no linker image exceeds the conservative envelope;
- candidate OTA identity matches `0x100B/0x020C`, not the generic reference tuple.

## Phase 3 — acquire and pin the build stack

Two build tracks may be maintained until one is clearly superior.

### Track A — TuyaOS-native reference build

Preferred when public Tuya tooling/source can reproduce the Lighting Product Development Kit.

Pin:

- TuyaOS Zigbee platform source/tool release;
- application source revision;
- compiler/toolchain version;
- Python/CMake/build dependencies;
- any closed binary libraries by exact hash if redistribution permits only references, not vendoring.

Goal: reproduce a clean unmodified TS0505B/ZSU reference build and obtain QIO/UG artifacts.

### Track B — Silicon Labs application reconstruction

Fallback if Tuya's published application cannot be built reproducibly outside Tuya's IDE/tooling.

Use current SiSDK/EmberZNet for MG21 and reproduce:

- endpoint 1 Extended Color Light;
- Basic/Identify/Groups/Scenes/OnOff/Level/Color Control;
- OTA client and storage bootloader compatibility assumptions;
- Tuya manufacturer/model identity where safe;
- required Tuya-specific application behavior;
- five-channel RGBCW adapter;
- NVM/rejoin behavior.

Track B must not be treated as OTA-deployable merely because it builds; bootloader/container compatibility must be independently demonstrated.

### Exit criteria

- exact toolchain versions recorded;
- clean build command/script exists;
- CI can validate source/config even if proprietary SDK binaries cannot legally be redistributed;
- deterministic or explainably reproducible application bytes are produced.

---

## Phase 4 — reproduce stock-compatible lighting behavior

### Standard Zigbee behavior

Implement/test:

- On/Off;
- Move to level;
- Move to level with On/Off semantics;
- Color temperature;
- XY/HSV color if exposed;
- Groups;
- Scenes;
- Identify;
- reporting/readback;
- startup/rejoin behavior.

### Exact known stock bug to eliminate

For `_TZ3210_mja6r5ix` app 112 / `z.1.0`, `moveToLevelWithOnOff` can leave physical and reported state inconsistent. Candidate behavior must keep:

- physical output;
- `genOnOff.onOff`;
- `genLevelCtrl.currentLevel`

synchronized after Off→On + brightness transitions.

### Tuya private behavior

Preserve only what is necessary for compatibility. Avoid periodic proprietary chatter that gives no functional value.

### RGB+CCT adapter

Reference mapping from Tuya's kit:

- R PA3;
- G PD2;
- B PC5;
- CW PA4;
- WW PA0.

Keep these behind a board-profile abstraction. Preserve configurable polarity, PWM frequency, duty limits, CCT bounds, power limits and gamma/white balance.

### Exit criteria

Host/unit/simulation tests cover cluster state transitions and output mapping logic; no installed bulb write yet.

---

## Phase 5 — router reliability implementation

### Router v0 configuration

- router / receiver-on-idle;
- neighbor table 26;
- route table 16;
- discovery table 8;
- address table 12;
- broadcast table 15;
- no concentrator;
- no periodic many-to-one originator;
- source-route support as required by the stack;
- normal route discovery/repair;
- NVM persistence/rejoin.

### Why only neighbor table increases first

The production mesh has >100 Zigbee devices. A larger neighbor table gives a mains router more capacity to retain useful neighbor relationships at very low RAM cost while avoiding destabilizing broad network-level tuning.

Do not increase broadcast table, route table or discovery table until measured production evidence identifies exhaustion/churn there.

### Diagnostics

Expose or log on demand where feasible:

- reset reason;
- uptime/boot count;
- stack counters;
- route discovery failures;
- APS retries/failures;
- MAC retries/failures;
- neighbor table occupancy;
- route table occupancy;
- rejoin reason/state.

Diagnostics must be query-driven or local; do not turn them into frequent Zigbee reports.

### Exit criteria

- router config verified by CI/parser;
- flash/RAM delta recorded;
- no periodic traffic regression introduced.

---

## Phase 6 — OTA container reconstruction and policy analysis

### Artifact chain

For every candidate preserve:

`source SHA -> application image -> GBL/UG -> Zigbee OTA wrapper/index -> SHA-256`

Record:

- application version;
- Zigbee manufacturer code;
- image type;
- file version;
- header string;
- minimum/max hardware version if used;
- payload size;
- GBL type/version;
- signature/encryption indicators.

### Signed/encrypted bootloader risk

Silicon Labs Gecko Bootloader can enforce signed and/or encrypted firmware upgrade files. The production Tuya setting is unknown.

Analyze without installation where possible:

- public Tuya UG examples;
- any downloadable Tuya stock images for ZSU/MG21 with same OTA family;
- GBL tags/headers;
- evidence of signature tags;
- Zigbee OTA wrapper structure;
- bootloader generation defaults in Tuya's platform.

Do not attempt to defeat signature enforcement. If the production bootloader requires a Tuya private key, OTA replacement firmware is blocked by design and the project stops at that boundary.

### Exit criteria

A candidate OTA package can be fully parsed and its identity exactly matches the live tuple. Bootloader acceptance risk is classified as low/medium/high with evidence.

---

## Phase 7 — rollback strategy without physical access

### Preferred rollback

Find a verified stock firmware image compatible with:

- `_TZ3210_mja6r5ix` or demonstrably the same product PID/OTA identity;
- live manufacturer code;
- live image type;
- compatible file/hardware version.

Record SHA-256 and source provenance.

### If no stock image exists

Do not pretend rollback is solved. The first canary may proceed only after explicit review if all of these are true:

- OTA transport is standard and stable;
- candidate container is structurally valid;
- bootloader validates the image before swapping applications;
- a failed verification should leave stock firmware running;
- the canary is expendable from a functional perspective;
- user explicitly accepts the residual risk that successful installation plus bad application behavior may not be OTA-recoverable.

No-disassembly means a truly bricked application may be unrecoverable. This residual risk must be stated immediately before first OTA authorization.

### Exit criteria

Rollback status is classified honestly as VERIFIED / BOOTLOADER-REJECT-SAFE ONLY / UNRESOLVED.

---

## Phase 8 — build-only release candidate

Produce a release-candidate manifest containing:

- source SHA;
- toolchain/SDK revisions;
- build command;
- compiler warnings;
- flash/RAM usage;
- application SHA-256;
- GBL/UG SHA-256;
- OTA wrapper SHA-256;
- parsed OTA identity;
- router config snapshot;
- application compatibility test results;
- bootloader-policy risk;
- rollback classification;
- exact intended canary.

CI must fail if:

- router policy drifts;
- OTA manufacturer/image type changes unexpectedly;
- candidate exceeds conservative flash bounds;
- prohibited concentrator/many-to-one options appear;
- version does not advance correctly;
- required lighting clusters disappear.

---

## Phase 9 — canary authorization package

Default canary: choose the least critical Hall bulb after fresh live metrics; do not select solely by IEEE order.

Immediately before asking for authorization:

- confirm the bulb is currently reachable;
- capture fresh LQI and health state;
- verify stock version/OTA tuple again;
- verify candidate hashes against CI;
- verify OTA index points only to the intended candidate;
- make sure no automatic fleet OTA rule exists;
- prepare exact Zigbee2MQTT one-device update request;
- define stop conditions.

### Stop conditions during OTA

Abort/no retry loop if:

- metadata mismatch;
- unexpected image request parameters;
- transfer repeatedly times out;
- device leaves unexpectedly;
- bootloader rejects verification;
- coordinator/mesh error rate spikes.

Do not switch to another bulb to “see if it works.” Diagnose first.

---

## Phase 10 — canary postflight

Immediately after successful boot:

1. confirm join/rejoin and same IEEE identity;
2. confirm Basic cluster/version;
3. On→Off→On;
4. brightness 1/10/50/100%;
5. color temperature warm/mid/cool;
6. R/G/B low then moderate brightness;
7. mixed white/color transitions;
8. verify reported state after each command;
9. group/scene behavior if used;
10. power-cycle recovery;
11. coordinator/Zigbee2MQTT restart recovery;
12. capture diagnostics/counters.

Any wrong channel, inability to turn fully off, uncontrolled full-power output, reset loop, join instability or major mesh regression is failure.

---

## Phase 11 — measured router soak

### Minimum 24 h, preferred 72 h

Compare stock baseline vs canary:

- ZCL command timeout rate;
- median/p95 command latency;
- APS/MAC retry/failure counters where available;
- route/source-route failure log frequency;
- leave/rejoin count;
- network-address changes;
- neighbor-table occupancy/stability;
- evidence that children/other routers can route through it when selected by the mesh;
- reset/watchdog count;
- bulb functional correctness.

Success is not “LQI went up.” Success is lower failure/churn with no new mesh pathology.

---

## Phase 12 — rollout decision

### GO

Only if the canary passes functional postflight and the soak shows no regression, preferably measurable improvement.

Roll out one additional bulb, observe, then the third. Do not update all remaining bulbs simultaneously.

### HOLD

Use when behavior is correct but router improvement is inconclusive. Keep one canary longer and collect more evidence.

### STOP

Use when:

- signed bootloader blocks custom OTA;
- RGB+CCT mapping is incompatible;
- route behavior regresses;
- device resets/rejoins;
- no practical no-disassembly recovery exists and application risk remains too high.

---

## Current immediate work queue

1. Read-only OTA check on target-a and save the exact tuple.
2. Search/pin TuyaOS ZSU lighting source/build tooling and determine whether the published kit can be reproduced headlessly.
3. Add OTA parser/manifest tooling to this repo.
4. Add machine-readable live-device evidence.
5. Build the unmodified reference target before any router modification.
6. Integrate router v0 and state/brightness correctness fixes.
7. Produce deterministic build-only candidate and CI artifact manifest.
8. Continue stock-image/bootloader-signature research.
9. Stop only when the next meaningful action is the first actual one-device OTA update.
