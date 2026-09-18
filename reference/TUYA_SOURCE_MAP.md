# Pinned Tuya public source map

This file records public source/reference inputs used for the TS0505B build design. It is evidence, not proof that the installed `_TZ3210_mja6r5ix` application bytes are identical.

## Public GitHub reference

Repository: `tuya/tuya-iotos-embeded-demo-zigbee-sdk-development-course`

Pinned commit: `cdf8dfe6d545aedd78210da50288c4bf300892f8`

License: MIT (`LICENSE` blob `4b2cfb22f6317c808434fa991a3d5587e8aff447`).

### `tuyaos_demo_zigbee_switch/appconfig.json`

Published firmware identity example:

- module: `ZSU`
- role: `ROUTER`
- chip: `EFR32MG21A020F1024`
- OTA image type: `0x1602`
- OTA manufacturer: `0x1002`
- Tuya manufacturer capacity prefix: `_TZ3210_`

This independently aligns with the current Tuya Lighting Product Development Kit.

### `tuyaos_demo_zigbee_pwm/include/tuya_pwm_demo.h`

Relevant MG21 implementation clues:

- `MG21_FLASH_PAGE_SIZE = 8 * 1024`
- reset-count persistence address `0xE4000`
- application-data persistence on the next 8 KiB page
- MG21 logical GPIO mapping includes PA/PC/PD pins used by lighting examples
- Zigbee heartbeat range starts at 150 s in this older demo

These addresses strongly indicate a 1 MiB MG21 build in this public sample, but they must not be copied blindly into a candidate linker layout.

### `tuyaos_demo_zigbee_pwm/src/tuya_sdk_callback.c`

The public demo configures:

- node type `ZG_ROUTER`
- transmit power `11` dBm
- normal network join configuration
- On/Off, Groups, Scenes, Level and Color-related application clusters

The older PWM demo endpoint descriptor is not the modern TS0505B Extended Color Light descriptor, so use current Lighting PDK documentation for the target endpoint/cluster model.

## Current Tuya Lighting PDK reference

Authoritative family-level configuration documents:

- model `TS0505B`
- manufacturer `_TZ3210_<PID>`
- router role
- module `ZSU`
- chip `efr32mg21a020f1024im32` with documented `efr32mg21a020f768im32` alternative
- OTA manufacturer `0x1002`
- image type `0x1602`
- endpoint 1 Extended Color Light
- RGBCW reference pins R=PA3, G=PD2, B=PC5, CW=PA4, WW=PA0
- QIO production and UG OTA build outputs

TuyaOS documents `build_app.sh` as the actual command-line build entry point. Preferred reproducible build path is therefore headless TuyaOS rather than GUI-only automation.

## Evidence rule

Live interrogation has resolved this gate in the **mismatch** direction. target-a and target-b independently report OTA manufacturer `0x100B`, image type `0x020C`, file version `0x10003607`, while the public Tuya reference remains `0x1002/0x1602`.

Therefore the public Tuya material is retained as platform/application reference evidence only. It must not be promoted directly to the installed-device binary/OTA envelope unless the OEM identity difference and bootloader compatibility are independently reconciled. Any deployable candidate must target the measured live tuple.
