# Public compatibility research — 2026-09-18

## Findings

Tuya's current Lighting Product Development Kit still documents TS0505B as a router on the ZSU module, using EFR32MG21A020F1024IM32 with a documented 768 KiB alternative. Its generic reference OTA identity is 0x1002/0x1602, so it remains family/platform evidence rather than proof for the measured OEM tuple.

An independent openHAB fingerprint of the exact `_TZ3210_mja6r5ix` / `TS0505B` family reports application 112, build `z.1.0`, OTA current file version 268449287 (`0x10003607`), and manufacturer ID 4107 (`0x100B`). This independently corroborates the unusual manufacturer code/file-version lineage, but does not provide a usable `0x020C` stock image.

Public reports also show `0x10003607` on unrelated Tuya devices. Therefore that outer OTA version is not treated as a unique firmware-family identifier and must not be reused as an internal Gecko Application Properties version.

Current Silicon Labs documentation exposes bootloader capability flags for enforced upgrade signatures, encryption, GBL parsing/storage, and rollback protection. Rollback protection checks the internal Application Properties version before applying an upgrade. If no candidate image passes bootloader verification, the bootloader can return to the existing application; however an interrupted application upgrade can still leave a device without a working application.

## Sources

- Tuya Lighting PDK: https://developer.tuya.com/en/docs/iot-device-dev/tuyaos_zigbee_light_product_development_kit?id=Kd6efghkquo9d
- exact-family openHAB fingerprint: https://community.openhab.org/t/zigbee-bulb-not-changing-colors/156269/10
- unrelated Tuya device using the same outer version: https://github.com/Koenkk/zigbee2mqtt/issues/24218
- Gecko Bootloader common capability interface: https://docs.silabs.com/mcu-bootloader/latest/gecko-bootloader-api/common-interface
- Gecko Bootloader rollback/security behavior: https://docs.silabs.com/shared-content/1.0.1/bootloader-user-guide-series3-and-higher/09-gecko-bootloader-security-features
- Gecko Bootloader upgrade/error handling: https://docs.silabs.com/mcu-bootloader/latest/bootloader-user-guide-series3-and-higher/03-gecko-bootloader-operation-application-upgrade

## Result

No trustworthy public stock OTA/GBL for exact `0x100B/0x020C` + `_TZ3210_mja6r5ix` was found in the current public search. The correct next milestone is therefore a layout-compatible, deliberately safe diagnostic canary design plus continued stock-image/bootloader evidence collection—not header spoofing or a blind OTA attempt.
