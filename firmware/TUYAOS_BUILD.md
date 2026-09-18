# TuyaOS ZSU/TS0505B build path

## Preferred build track

Use the current TuyaOS Zigbee Lighting Product Development Kit as the application baseline, because it already models the device family we need:

- `TS0505B`
- `_TZ3210_<PID>`
- router
- `ZSU`
- `EFR32MG21A020F1024IM32` / documented 768 KiB alternative
- OTA manufacturer `0x1002`
- OTA image type `0x1602`
- Extended Color Light
- RGB+CCT
- QIO production output + UG OTA output

The GUI is optional. Tuya documents `build_app.sh` as the command-line build entry point.

## Required local framework layout

A TuyaOS development framework is expected to contain at least:

- `build_app.sh`
- `Makefile`
- `scripts/mk/`
- `vendor/<target>/tuyaos/tuyaos_adapter/`
- `apps/<application>/`

The build system may fetch/install target vendor tooling under `vendor/`; do not commit proprietary/downloaded toolchain blobs to this repository unless their license explicitly permits redistribution.

## Canonical headless invocation

From the TuyaOS framework root:

```sh
sh build_app.sh apps/<APP_NAME> <APP_NAME> <VERSION>
```

For a clean rebuild:

```sh
sh build_app.sh apps/<APP_NAME> <APP_NAME> <VERSION> clean
sh build_app.sh apps/<APP_NAME> <APP_NAME> <VERSION>
```

The version must be deliberately controlled; candidate versioning must not accidentally collide with the stock OTA `fileVersion` policy.

## First milestone: unmodified reference build

Before changing router behavior:

1. obtain the exact Lighting PDK/framework legally through Tuya's normal developer path;
2. record framework/package version and cryptographic hashes of downloaded archives where practical;
3. preserve the original app as `reference` in the local worktree;
4. configure ZSU + MG21 target;
5. configure the **reference control build** as `TS0505B`, router, manufacturer `0x1002`, image type `0x1602`; do not use this tuple for the installed bulbs;
6. build without router-policy modifications;
7. preserve QIO and UG artifacts;
8. parse the UG/OTA header and document the expected mismatch against live `0x100B/0x020C/0x10003607`; use the reference artifact only for structural/platform analysis until compatibility is reconciled;
9. record flash/RAM output and artifact hashes.

An unmodified reference build is the control sample for all later candidate diffs.

## Application identity

Do not invent a new Zigbee model/manufacturer string during bring-up. Preserve the family behavior expected by Zigbee2MQTT while avoiding falsely claiming a vendor-signed stock version.

The exact final Basic-cluster version/manufacturer policy must be reviewed before deployment because:

- Zigbee2MQTT fingerprints the exact manufacturer/model;
- OTA matching uses manufacturer code + image type + file version;
- the Tuya manufacturer string contains the product PID;
- a custom firmware version must be distinguishable for diagnostics without breaking the converter.

## Reference lighting configuration

Use Tuya's current reference as the initial board profile:

- channels: RGBCW (`APP_LIGHT_CHANNELS=5` equivalent)
- R: PA3
- G: PD2
- B: PC5
- Cold: PA4
- Warm: PA0

Keep all output properties configurable:

- PWM frequency
- PWM polarity
- minimum/maximum RGB duty
- minimum/maximum white duty
- RGB power cap
- white power cap
- CCT min/max
- gamma
- white balance
- startup state
- Tuya private command enablement

The reference mapping is not by itself authorization to flash a production bulb.

## Router patch strategy

Prefer the narrowest integration point that changes stack configuration without rewriting Tuya's application behavior.

Initial router policy:

- router / receiver on when idle
- neighbor table 26
- route table 16
- discovery table 8
- address table 12
- broadcast table 15
- no concentrator
- no periodic many-to-one originator

If TuyaOS abstracts or fixes these EmberZNet compile-time values inside prebuilt libraries, document which values are externally configurable and which are not. Do not binary-patch closed libraries.

If neighbor-table size cannot be changed through supported source/configuration, the alternative is to rebuild the Zigbee stack using a compatible Silicon Labs application path; that becomes Track B and requires separate OTA/container compatibility proof.

## Reproducibility record

Every build should capture:

- repository source SHA
- TuyaOS framework version/hash
- target platform/module
- compiler version
- build command
- application version
- relevant configuration diff
- linker memory usage
- QIO SHA-256
- UG SHA-256
- parsed Zigbee OTA identity

## Deployment prohibition

QIO is never a deployment artifact for this no-disassembly project.

Only the UG/OTA path is eligible for a future canary, and only after the F2 authorization gate.