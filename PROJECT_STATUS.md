# Project status

Updated: 2026-09-18

## State

**PUBLIC-QUALITY SOURCE / OTA-FIRST BRING-UP / NO DEVICE WRITE**

The engineering tree now has a privacy-sanitized public-release path, cross-platform quality gate, public-hygiene validator, and machine-readable flashability gate. Repository, router policy, safety gates, CI validation and stock reliability baseline are established. No installed bulb has been modified. **Bulb disassembly is a hard project constraint: do not use teardown/SWD/JTAG as a planned recovery path.**

The live OTA tuple is captured and corroborated, and the frozen D0 artifact now has an independently verified flash-layout proof. The active blockers are production bootloader acceptance/recovery policy and exact installed platform/storage compatibility; the generic Tuya OTA identity remains reference-only.

## Live installed targets

| Device | IEEE | Role | Stock build |
|---|---|---|---|
| `target-a` | `IEEE_REDACTED_A` | Router | `z.1.0` / app 112 |
| `target-b` | `IEEE_REDACTED_B` | Router | `z.1.0` / app 112 |
| `target-c` | `IEEE_REDACTED_C` | Router | `z.1.0` / app 112 |

Shared fingerprint: `TS0505B` / `_TZ3210_mja6r5ix`; HA model `TS0505B_1_1`; stack 2; hardware 0; endpoint 1 Extended Color Light; OTA client/output cluster present.

## Stock reliability baseline

Production Zigbee2MQTT logs from 2026-09-09 contain confirmed 10-second application timeouts on stock firmware:

- target-c: two On/Off reads timed out;
- target-a: Color Control `moveToColorTemp` timed out;
- target-c: Color Control `moveToColorTemp` timed out.

The same session reported usable but variable LQI and no leave/network-address changes. See `evidence/stock-baseline-2026-09-09.md`. The canary target is command/reachability stability, not simply higher LQI.

## Platform evidence — live OTA identity captured

Tuya's published TS0505B/ZSU material remains authoritative **family/reference** evidence: `TS0505B`, `_TZ3210_<PID>`, router role, ZSU/EFR32MG21, RGB+CCT application, and reference OTA identity `0x1002/0x1602`.

The installed `_TZ3210_mja6r5ix` population does **not** use that generic OTA identity. Two independent device-originated Query Next Image requests measured:

- manufacturer code `0x100B` (`4107`);
- image type `0x020C` (`524`);
- installed file version `0x10003607` (`268449287`);
- field control `0`.

target-a and target-b returned the exact same tuple. target-c did not emit Query Next Image during its probe window while ordinary Zigbee traffic remained visible. By project decision it is treated as the same production population because its stock fingerprint is identical; its `0x100B/0x020C/0x10003607` identity is inferred rather than independently measured, and it is not eligible as the first canary.

The live tuple is now authoritative for OTA candidate targeting. The generic `0x1002/0x1602` tuple must never be used to target these installed bulbs. ZSU/EFR32MG21 remains the leading platform envelope, but binary/bootloader compatibility is `UNRESOLVED_IDENTITY_MISMATCH` until the OEM identity difference is explained. See `evidence/live-ota-probe-2026-09-10.md` and `evidence/oem-identity-analysis-2026-09-10.md`.

## RGB+CCT reference evidence

Tuya publishes the reference five-channel pin assignment:

- R PA3
- G PD2
- B PC5
- Cold White PA4
- Warm White PA0

The application exposes PWM frequency/polarity, power limits, duty ranges, CCT range, gamma/white balance, startup behavior and Tuya-private-command enablement as configuration. Treat this mapping as the build/reference baseline, not as absolute proof of every production PCB revision.

## OTA/recovery position

A Zigbee2MQTT manual OTA **check** does not initiate firmware installation. The decisive tuple is captured from the resulting debug `commandQueryNextImageRequest`, which includes manufacturer code, image type and file version.

The OTA cluster does not guarantee acceptance of arbitrary custom bytes. Silicon Labs Gecko Bootloader can optionally require signed/encrypted GBL files and can enforce rollback protection using the **internal GBL Application Properties version**. That version is distinct from the outer Zigbee OTA file version. The exact Tuya production signing, encryption, rollback and acceptance policy remains unresolved.

The frozen D0 diagnostic container is now independently verified: OTA `0x100B/0x020C/0x10003608`, unsigned/unencrypted GBL3 Application Properties version `1`, and exactly two ERASEPROG ranges `0x4000..0x4234` and `0x4238..0x4E548`. The highest erased page ends at `0x50000`, below even the conservative 768-KiB envelope, with no bootloader or SE-upgrade payload. This proves the candidate's flash-write layout, not stock bootloader acceptance. No exact stock `_TZ3210_mja6r5ix` internal application version or rollback image has been verified, so rollback/acceptance remains **UNRESOLVED** and the D0 OTA is still non-deployable.

## Development baseline

Tuya's TS0505B/ZSU lighting conventions remain the preferred reference for identity, endpoint/cluster behavior, RGB+CCT control and UG OTA packaging. The parallel Silicon Labs reconstruction track has now crossed its first build gate.

Using the official Simplicity SDK 2026.6.1 Z3 Light template, a board-neutral `EFR32MG21A020F1024IM32` routing reference and router-v0 both compile and link successfully. Router-v0 changes only the neighbor table from 16 to 26; route=16, discovery=8, address=12 and broadcast=15 remain unchanged, and the concentrator component is absent.

The 26-neighbor change costs +216 B aligned BSS, exactly offset by -216 B from the generated memory-manager heap, with no `.text`, `.data` or BIN-size growth. A clean direct-from-template rebuild produced the identical router-v0 BIN SHA-256 `6c88a93bb9f5eb05145ca7a4dd8d6dd3a80febd42c97a4e62013701fdbe8c3b3`.

The board-neutral light-state/ZCL layer now also compiles and links cleanly on that router-v0 envelope. It adds only **224 B of `.text`/BIN and 0 B RAM**. Two clean builds and a completely independent seed regenerated from the pinned official Z3 Light template all produced the identical 305468-byte BIN SHA-256 `2ca1d42aca7d1b5bc47cdeb460ff2f74e25f1a1108c1a1b13531b3d9fc412ba6`.

The independent regeneration exposed Silicon Labs template auto-selection of development-board LED/button instances. Those components are now explicitly excluded rather than assigning guessed pins. The physical board output remains a weak no-op and the custom light sources contain no GPIO/PWM or Tuya reference pin mapping.
The logical renderer now mirrors ZCL On/Off, level and color state exactly; minimum-duty translation is explicitly forbidden in the logical core. With the weak no-op board hook and LTO, that source-only correction does not alter the structural BIN hash, so host tests remain the authority for state-contract behavior.

The exact installed application descriptor is now structurally build-proven as well: one endpoint `1`, HA profile `0x0104`, Extended Color Light `0x010D`, the live eight-server/two-client cluster set, and generated Basic strings `_TZ3210_mja6r5ix` / `TS0505B`. Two independent clean source-to-artifact generations produced the identical **304440-byte** BIN SHA-256 `b9cd57674051d9239489f639f017b5be112329743ce861ca9f84ae82ba573042`. Compared with the prior lightcore build, endpoint parity reduces BIN size by 1028 B. ZAP manufacturer-code metadata is `0x100B`, but this is not treated as proof of Node Descriptor or bootloader acceptance; the live outer OTA identity is measured, while the final candidate runtime/container contract remains unresolved.

This is **structural build evidence only**. The exact installed PCB/flash-density part is not directly proven, no production GPIO mapping has been assumed, and the build is not OTA/deployment eligible.

## Implemented software-only tooling

- `docs/EXECUTION_PLAN.md` - full phased implementation plan;
- `docs/CANARY_RUNBOOK.md` - read-only preflight, F2 boundary and postflight/soak procedure;
- `firmware/target_manifest.json` - fail-closed target/live/candidate/rollback state;
- `firmware/reference_build_manifest.json` - generic Tuya reference-control build record, explicitly non-deployable;
- `firmware/silabs_router_v0_build_manifest.json` - pinned structural MG21 reference/router-v0 build, memory deltas and deterministic hashes;
- `firmware/SDK_BASELINE.md` - pinned Silicon Labs toolchain and direct vendor-template reproduction path;
- `firmware/TUYAOS_BUILD.md` - reproducible headless TuyaOS build strategy;
- `reference/TUYA_SOURCE_MAP.md` - pinned public Tuya source evidence;
- `evidence/silabs-router-v0-build-2026-09-10.md` - successful router build/rebuild evidence;
- `evidence/silabs-lightcore-build-2026-09-11.md` - board-neutral lightcore ARM build and independent source-to-artifact reproduction;
- `evidence/silabs-endpoint-v0-build-2026-09-11.md` - exact endpoint/Basic-identity ARM build and independent byte-for-byte reproduction;
- `firmware/endpoint_profile.json` + endpoint transformer/verifier - fail-closed installed endpoint-1 structural contract;
- `firmware/app/` - board-neutral light-state model and ZCL adapter with a deliberately no-op physical output hook;
- `evidence/structural-container-v0-2026-09-11.md` - unsigned structural GBL3/OTA proof and bootloader-version separation;
- OTA/GBL parsing and unified artifact-inspection tools with separate target-match and deployment-ready gates;
- CI validators for router policy, live target safety and structural build evidence.
- `firmware/board_profiles/tuya_zsu_ts0505b_reference.json` - machine-checked Tuya reference PWM mapping, explicitly non-deployable;
- `tools/quality_gate.py` plus public hygiene/flashability validators - one-command source-quality gate and explicit deployment blocker ledger;
- `firmware/canary_d0_manifest.json` + `tools/preflight_d0_candidate.py` - frozen D0 identity/ranges and byte-for-byte pre-staging gate;
- `tools/patch_zigbee_herdsman_d0_hold.py` + `docs/D0_VALIDATION_HOLD.md` - tuple-scoped validation-only Upgrade End hold, verified against zigbee-herdsman 10.9.4;
- `evidence/d0-flash-layout-verification-2026-09-18.md` - independent ERASEPROG/range/CRC verification record;
- `docs/FLASHABILITY.md`, `docs/DIAGNOSTIC_CANARY.md`, `docs/PUBLIC_RELEASE.md` - canary-ready contract, diagnostic-first candidate design and fresh-history public-release model;
- `evidence/public-research-2026-09-18.md` - updated Tuya/exact-family/Silicon Labs compatibility research.

No tooling is permitted to publish an OTA update request or flash a device.

## Current live dependency

Live OTA identity capture is complete for target-a and independently corroborated by target-b. The Silicon Labs MG21 router-v0, board-neutral light-state layer, exact endpoint/fingerprint profile, D0 container identity, and D0 flash-write envelope are now structurally proven and reproducible. For the dark diagnostic canary, the remaining safety blockers are exact installed platform/storage compatibility, stock internal GBL Application Properties version, bootloader rollback/signature/encryption acceptance policy, and a no-disassembly rollback/reject-safe classification. The physical RGB+CCT output contract remains a blocker for a lighting-capable release, but D0 deliberately keeps physical output inert.

The temporary Zigbee2MQTT OTA-probe converter has been removed, persisted logging is back to `info`, and the production add-on restarted cleanly after the probe.

## Execution order from here

1. Keep `0x100B/0x020C/0x10003607` authoritative for the installed population and `0x1002/0x1602` reference-only.
2. Preserve the deterministic Silicon Labs router-v0 build as structural evidence; do not promote its MG21 part assumption to installed-PCB proof.
3. Preserve the now build-proven board-neutral light-state/ZCL layer and keep the physical output hook inert until the production board contract is independently supported.
4. Preserve the now build-proven exact endpoint/device-type/Basic identity contract; keep runtime OTA identity and physical PWM behind unresolved deployment gates.
5. Resolve the stock internal GBL Application Properties version separately from outer OTA `0x10003607`; do not infer one from the other.
6. Continue exact OEM/stock image and `0x100B/0x020C` bootloader research, including rollback/signature/encryption policy; acquire TuyaOS ZSU Lighting PDK/framework if available.
7. Parse any trustworthy UG/GBL candidate for security flags, program ranges and OTA identity. QIO remains forbidden for deployment.
8. Keep deterministic source-to-artifact hashes and `deployment_ready=false` until binary compatibility, bootloader acceptance and rollback/reject-safe gates are resolved.
9. Keep the frozen D0 manifest and `tools/preflight_d0_candidate.py` as the byte-for-byte staging authority; target-c remains excluded as first canary.
10. Use `docs/D0_VALIDATION_HOLD.md` for the first authorized live experiment. Fresh 2026-09-18 production logs currently favor target-b over target-a for the first canary because target-b shows fewer genuine timeout/error events while remaining online on the same stock build; re-check immediately before mutation. Prefer the reversible Zigbee2MQTT external-extension hold, and stop immediately before the first OTA-storage mutation for explicit user authorization. A successful held transfer is verification-acceptance evidence only; custom-application activation remains a separate authorization boundary.
