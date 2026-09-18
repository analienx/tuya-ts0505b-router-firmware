# Silicon Labs exact HallBulb endpoint-v0 build — 2026-09-11

## Scope and safety

This milestone proves the installed HallBulb Zigbee application descriptor and Basic-cluster identity on the existing board-neutral MG21 structural build. It is **software-only structural evidence**: no OTA container was produced and no installed bulb was queried for an update, written, erased, opened, or connected to a programmer.

The physical RGB+CCT output remains `weak_noop`. No production GPIO/PWM mapping is present. The live OTA target remains `0x100B/0x020C` at stock file version `0x10003607`, but runtime OTA image identity is intentionally unresolved in this build and `deployment_eligible=false`.

The ZAP `manufacturerCodes` metadata is set to `0x100B` because that value matches the installed population's observed manufacturer code. This is generation metadata only; it is **not** treated as proof of the Zigbee Node Descriptor manufacturer code, the OTA image type/file version, or bootloader acceptance.

## Exact endpoint profile

The repo-owned `firmware/endpoint_profile.json` and transformer produce exactly one application endpoint:

- endpoint `1`;
- Home Automation profile `0x0104` (`260`);
- Extended Color Light device type `0x010D` (`269`);
- server clusters: Basic `0x0000`, Identify `0x0003`, Groups `0x0004`, Scenes `0x0005`, On/Off `0x0006`, Level `0x0008`, Color Control `0x0300`, ZLL/Touchlink `0x1000`;
- client clusters: Time `0x000A`, OTA Upgrade `0x0019`;
- Basic manufacturer name `_TZ3210_mja6r5ix`;
- Basic model identifier `TS0505B`.

`tools/apply_silabs_endpoint_profile.py` applies that contract idempotently and fails closed if the Extended Color Light source endpoint, a required cluster, or the Basic identity attributes are absent. `tools/verify_endpoint_profile.py` independently validates the transformed ZAP file.

Generated `autogen/zap-config.h` confirms one fixed endpoint, profile `260`, device `269`, ten generated clusters with the eight-server/two-client split above, and compile-time Basic strings for the exact installed manufacturer/model.

## Clean ARM build

The profile was generated and linked with Simplicity SDK `2026.6.1`, Zigbee `9.1.1`, SLC `6.0.23`, ZAP `2026.6.18`, and GCC `14.2.1` for the structural `EFR32MG21A020F1024IM32` envelope.

| Metric | Lightcore baseline | Endpoint-v0 | Delta |
|---|---:|---:|---:|
| `.text` | 300896 B | 299916 B | **-980 B** |
| `.data` | 3984 B | 3936 B | **-48 B** |
| `.bss` | 14836 B | 14192 B | **-644 B** |
| memory-manager heap | 74968 B | 75660 B | **+692 B** |
| BIN | 305468 B | 304440 B | **-1028 B** |

Endpoint-v0 BIN SHA-256:

`b9cd57674051d9239489f639f017b5be112329743ce861ca9f84ae82ba573042`

The endpoint/fingerprint adaptation therefore carries no flash-size penalty relative to the prior lightcore structural build; it reduces the linked BIN by 1028 bytes.

## Independent source-to-artifact reproduction

A second tree was generated independently from the official Silicon Labs Z3 Light template using `slc generate --new-project`, the bare MG21 compile target, RTT, explicit removal of `simple_led`/`simple_button`, and only `SL_ZIGBEE_NEIGHBOR_TABLE_SIZE=26` as a router override. The lightcore overlay and endpoint transformer were then applied before a fresh SLC generation and clean 372-step ARM build.

The independent artifact was compared with the first endpoint-v0 build:

- bytes: `304440` vs `304440`;
- SHA-256: identical `b9cd57674051d9239489f639f017b5be112329743ce861ca9f84ae82ba573042`;
- byte-for-byte comparison: **equal**;
- sections: `.text 299916`, `.data 3936`, `.bss 14192`, managed heap `75660`.

The Silicon Labs generator emits noisy type-discriminator messages from the vendor ZAP data set and a PTI-not-configured warning for this board-neutral target. Generation and both clean links completed successfully; no warning was suppressed by inventing board pins.

## Remaining deployment gates

This milestone closes the **structural endpoint/fingerprint parity** build gate. It does not prove the installed PCB/flash-density variant, RGB+CCT electrical output mapping, the Node Descriptor manufacturer-code source, the `0x100B/0x020C` OEM OTA container/bootloader contract, signing/encryption acceptance, or a no-disassembly rollback path.

`firmware/silabs_router_v0_build_manifest.json` schema 3 now records this artifact and its independent reproduction. `tools/verify_silabs_router_build_manifest.py` fails closed on endpoint, identity, hash, physical-output, OTA-pending, or deployment-state drift.

No custom firmware is deployment-ready and no device mutation is authorized by this evidence.
