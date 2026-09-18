# Executor contract — TS0505B router firmware

Read `.supervisor/project.yaml`, `PROJECT_STATUS.md`, `docs/BRINGUP.md`, and `docs/ROUTER_POLICY.md` before acting.

## Current authority boundary

The repository is in **software-only / OTA-first bring-up**. Read-only interrogation of Home Assistant/Zigbee2MQTT and local development-machine setup are in scope. Source, tests, CI and documentation may be changed under the normal supervisor/executor protocol.

The installed bulbs **must not be disassembled**. Treat this as a hard project constraint, not a fallback preference. Do not propose opening a bulb, probing internal pads, SWD/JTAG recovery, or destructive identification as a normal project path.

Do **not** flash, erase, unlock, mass-erase, alter bootloader/partition/OTA identity, trigger an OTA update, or perform any other persistent device mutation without explicit authorization covering that F2 boundary.

## Engineering rules

1. Platform confidence uses two distinct evidence layers: Tuya's published TS0505B/ZSU material is the EFR32MG21 family/reference baseline (`0x1002/0x1602`), while the installed `_TZ3210_mja6r5ix` population has independently measured live OTA identity `0x100B/0x020C` at file version `0x10003607`. The live tuple is authoritative for candidate targeting; the reference tuple is not. Binary compatibility remains unresolved until that OEM identity difference is explained.
2. Prefer the **Tuya TS0505B/ZSU lighting application conventions** for application identity, endpoint/cluster behavior, RGB+CCT configuration and OTA packaging. Use current Silicon Labs/EmberZNet knowledge for router-stack tuning where it can be integrated without breaking Tuya compatibility.
3. Preserve normal Zigbee light interoperability: Basic, Identify, Groups, Scenes, On/Off, Level Control and Color Control behaviour must remain standards-compatible. Also preserve any Tuya-specific behavior needed for Zigbee2MQTT compatibility.
4. The router goal is reliability, not maximal table numbers. Every non-default stack setting needs a stated reason and a test.
5. `SL_ZIGBEE_NEIGHBOR_TABLE_SIZE=26` is the initial deliberate router change. Keep route/discovery/address/broadcast conservative until production evidence justifies changes.
6. Do not make the bulb a concentrator. Many-to-one route requests are a coordinator/concentrator responsibility unless a later design review proves otherwise.
7. Preserve NVM/rejoin and recovery surfaces. A candidate without an OTA-safe recovery strategy is not deployable.
8. One canary first. Expansion to the other bulbs requires canary evidence.
9. Never use the published reference PWM mapping as proof of the installed board wiring. It is sufficient for a build-only candidate and compatibility research, but first deployment must include a reversible functional-output validation plan.
10. Never treat Zigbee2MQTT `supports_ota: false` alone as proof that the underlying bootloader lacks OTA. The decisive evidence is the live OTA query plus actual bootloader acceptance behavior.

## Required evidence before first candidate OTA

- live manufacturer code, image type and installed OTA file version from the exact canary;
- selected MG21 flash geometry justified from the Tuya module/application evidence and resulting build layout;
- bootloader/OTA acceptance analysis, including signed/encrypted GBL risk;
- candidate OTA/UG container whose identity matches the live device tuple;
- rollback strategy that does not require opening the bulb;
- RGB+CCT behavior test matrix and safe failure criteria;
- reproducible candidate build + SHA-256;
- Zigbee2MQTT baseline metrics and postflight acceptance plan.

Use issue #1 as the control/task ledger. Software work should continue autonomously until the only remaining step is a persistent OTA canary mutation requiring explicit authorization.