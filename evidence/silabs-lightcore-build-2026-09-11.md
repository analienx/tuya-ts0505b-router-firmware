# Silicon Labs MG21 board-neutral lightcore build — 2026-09-11

## Scope and safety

This milestone adds a board-neutral RGB+CCT logical state layer and a Silicon Labs ZCL adapter on top of the already build-proven router-v0. It is **software-only structural evidence**. No OTA container was produced and no installed bulb was modified.

The physical output hook is deliberately a weak no-op. There is no production GPIO/PWM implementation and the custom sources contain no Tuya reference pin names (`PA3`, `PD2`, `PC5`, `PA4`, `PA0`). The published Tuya pin map remains reference evidence only.

The live installed OTA identity remains `0x100B/0x020C` at `0x10003607`. Binary/bootloader compatibility and rollback remain unresolved, so this build is not deployment eligible.

## Application overlay

The repo-owned overlay consists of:

- `firmware/app/hallbulb_light_state.c/.h` — platform-independent On/Off, level, CT, HS and XY state/render logic;
- `firmware/app/hallbulb_zcl_adapter.c/.h` — reads authoritative ZCL attributes after application changes and renders them into the board-neutral output contract;
- `tools/apply_silabs_light_core.py` — idempotent seed-project patching plus generated-output source/header staging.

The state model keeps logical On/Off and level synchronized, including the stock-family failure mode where a level-with-on/off transition can otherwise leave physical and ZCL state inconsistent.
After final review, the renderer was tightened to mirror ZCL state exactly: there is no hidden `level 0 -> 1` floor or other minimum-duty translation in the logical core. Any future minimum-drive policy belongs only in a verified physical board profile. The host harness is the authoritative proof of this logical contract.

Because the current physical board hook is a weak no-op and the build uses LTO, the linker can optimize away parts of the render/output path. The corrected exact-state source therefore reproduces the same structural ARM BIN hash as the prior no-op build. This ARM artifact proves SDK/API/link integration, not runtime PWM behavior.
## ARM build result

The lightcore compiles and links cleanly against Simplicity SDK `2026.6.1`, Zigbee `9.1.1` and GCC `14.2.rel1` for the structural `EFR32MG21A020F1024IM32` compile envelope.

Two clean builds in the original generated tree completed all 372 build steps. The result is:

| Metric | Router-v0 | Router-v0 + lightcore | Delta |
|---|---:|---:|---:|
| `.text` | 300672 B | 300896 B | **+224 B** |
| `.data` | 3984 B | 3984 B | 0 B |
| `.bss` | 14836 B | 14836 B | 0 B |
| memory-manager heap | 74968 B | 74968 B | 0 B |
| BIN | 305244 B | 305468 B | **+224 B** |

Lightcore BIN SHA-256:

`2ca1d42aca7d1b5bc47cdeb460ff2f74e25f1a1108c1a1b13531b3d9fc412ba6`

Router tables remain neighbor=26, route=16, discovery=8, address=12 and broadcast=15. The concentrator remains absent.
## Independent source-to-artifact reproduction

A separate seed was generated directly from the pinned official Silicon Labs Z3 Light template rather than from the earlier working tree:

```text
slc generate --new-project \
  --project-file <SDK>/zigbee_app/z3/zigbee_z3_light/zigbee_z3_light.slcp \
  --sdk <SDK> --destination <seed> \
  --project-name hallbulb_z3_light_router_v0 \
  --with EFR32MG21A020F1024IM32,iostream_rtt \
  --without simple_led,simple_button \
  --configuration SL_ZIGBEE_NEIGHBOR_TABLE_SIZE:26 \
  --output-type cmake --toolchain gcc --trust-totality
```

The first independent attempt intentionally exposed an important hidden dependency: without the explicit `--without` list, SLC auto-selected development-board `simple_led` and `simple_button` instances. A bare MG21 build then failed because LED/button GPIO ports and pins were undefined. No pin values were invented to make it compile.

The regeneration was repeated with those board-only components explicitly excluded. The repo overlay was applied to the new seed, SLC generated a fresh CMake project, headers were staged by the overlay helper, and a clean ARM build completed successfully.
The independent output was byte-compared with the prior clean lightcore build:

- bytes: `305468` vs `305468`;
- SHA-256: identical `2ca1d42aca7d1b5bc47cdeb460ff2f74e25f1a1108c1a1b13531b3d9fc412ba6`;
- byte-for-byte comparison: **equal**;
- sections: `.text 300896`, `.data 3984`, `.bss 14836`, managed heap `74968`.

This demonstrates deterministic **source -> generated project -> ARM artifact** reproduction from the pinned official SDK template, not just repeated linking inside one generated checkout.

## Remaining gates

This milestone does not establish the exact installed PCB/flash-density part, the RGB+CCT electrical pin contract, Tuya bootloader signing/encryption policy, OTA-container compatibility, or rollback. The next build-only work can adapt endpoint/fingerprint semantics and keep the physical output behind the board-profile abstraction, but no candidate may become deployment-ready until the OEM container and no-disassembly recovery gates are resolved.
