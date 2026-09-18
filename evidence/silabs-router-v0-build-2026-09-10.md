# Silicon Labs MG21 router-v0 structural build — 2026-09-10

## Scope and safety

This evidence records a **software-only structural build**. No installed bulb was written, queried for an update, erased, opened, or connected to a programmer. No OTA container was produced. The resulting binary is **not deployment eligible**.

`EFR32MG21A020F1024IM32` is used because Tuya's published ZSU/TS0505B family material makes it the leading compile envelope. This build does not prove that the installed `_TZ3210_mja6r5ix` PCB uses that exact flash-density part.

## Pinned build environment

- Simplicity SDK: `2026.6.1`
- Zigbee / EmberZNet: `9.1.1`
- vendor template: `zigbee_app/z3/zigbee_z3_light/zigbee_z3_light.slcp`
- target: `EFR32MG21A020F1024IM32`
- SLC: `6.0.23`
- ZAP: `2026.6.18`, commit `f4385241a2684847d4df0259261bdf3595080548`
- GCC: `14.2.1`, Silicon Labs Arm GNU `14.2.rel1-b66`
- CMake used by the build: `3.30.2`
- Ninja: `1.12.1`
- Simplicity Commander: `1v24p3b1989` (post-build dependency only; no programming command used)

## Generation

The board-neutral router-v0 project was regenerated directly from the official vendor template with these semantic inputs:

```text
slc generate \
  -p <Simplicity-SDK>/zigbee_app/z3/zigbee_z3_light/zigbee_z3_light.slcp \
  -d <output> -name hallbulb_z3_light_router_v0 -o cmake \
  --sdk-package-path <Simplicity-SDK>/simplicity_sdk.slcs \
  --with EFR32MG21A020F1024IM32,iostream_rtt \
  --without simple_led,simple_button \
  --configuration SL_ZIGBEE_NEIGHBOR_TABLE_SIZE:26
```

Removing `simple_led` and `simple_button` avoids inventing development-board GPIO assignments for the unknown production bulb PCB. RTT is retained only as a board-neutral diagnostic console.

A direct `.slcp` comparison against the successful routing-reference project showed only the project name/label and `SL_ZIGBEE_NEIGHBOR_TABLE_SIZE=26` as semantic differences. Generated configuration confirms route=16, address=12 and broadcast=15; discovery remains the SDK default 8. The optional `zigbee_concentrator` component is absent.

SLC/ZAP emits upstream generator diagnostics for several ZCL struct/string discriminators, and the build emits a PTI-not-configured warning because no development-board PTI pins are assigned. Generation and compilation nevertheless both exit 0; these messages are not treated as proof of production suitability.

## Build result and measured delta

Both the 16-neighbor routing reference and 26-neighbor router-v0 compile and link successfully (370/370 build steps).

| Metric | Reference | Router-v0 | Delta |
|---|---:|---:|---:|
| neighbor entries | 16 | 26 | +10 |
| `.text` | 300672 B | 300672 B | 0 B |
| `.data` | 3984 B | 3984 B | 0 B |
| `.bss` | 14620 B | 14836 B | +216 B |
| memory-manager heap | 75184 B | 74968 B | -216 B |
| BIN | 305244 B | 305244 B | 0 B |

Symbol inspection attributes +180 B to `sli_zigbee_neighbor_data` (306 -> 486 B) and +40 B to `sli_zigbee_frame_counters_table` (92 -> 132 B). Linker alignment yields the measured +216 B BSS change; the generated memory-manager heap shrinks by exactly 216 B, leaving the overall reserved RAM footprint unchanged.

Reference BIN SHA-256: `2d81c5c8ccd4742d833a928d189150fabb20d9d74d98cf86016dcb9b926e80d8`

Router-v0 BIN SHA-256: `6c88a93bb9f5eb05145ca7a4dd8d6dd3a80febd42c97a4e62013701fdbe8c3b3`

A second clean regeneration directly from the official vendor template, using the same project name and pinned CMake 3.30.2/Ninja 1.12.1 toolchain, produced an **identical 305244-byte BIN with the same SHA-256**.

## Interpretation

The conservative router improvement is now demonstrated as buildable and extremely cheap in memory. It does **not** establish installed-PCB identity, RGB+CCT pin compatibility, Tuya bootloader acceptance, signed/encrypted GBL policy, OTA packaging compatibility, or rollback. Live targeting remains `0x100B/0x020C`, current file version `0x10003607`, while binary/bootloader compatibility and rollback remain unresolved.
