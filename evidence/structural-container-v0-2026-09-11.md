# Structural GBL/OTA container v0 — 2026-09-11

## Scope and safety

This evidence proves only that the reproducible endpoint-v0 ARM image can be wrapped into a syntactically valid Silicon Labs GBL3 file and then into a Zigbee OTA container using the measured live OTA header identity.

No OTA index was changed, no image was offered to Zigbee2MQTT, and no bulb received an update request or firmware bytes. The generated files remain build-scratch artifacts and are **not deployment candidates**.

Live outer Zigbee OTA baseline remains:

- manufacturer `0x100B`;
- image type `0x020C`;
- installed file version `0x10003607`;
- field control `0`.

The structural wrapper used outer file version `0x10003608` only to prove version-advance/header tooling.

## Structural GBL3 result

Input S37: deterministic endpoint-v0 build SHA-256 `b9cd57674051d9239489f639f017b5be112329743ce861ca9f84ae82ba573042` as recorded by the endpoint build evidence.

Simplicity Commander `1v24p3b1989` produced an unsigned, unencrypted GBL3:

- bytes: `304524`;
- SHA-256: `adea5ae30a1118c543b866f2bdff9a8c5a3820ad7577dd9a985452e1a87c589e`;
- GBL version: `0x03000000`;
- signed flag: false;
- encrypted flag: false;
- application type: Zigbee (`1`);
- ApplicationData version: **`1`**;
- product ID: all zero;
- program data starts at `0x00004000` and `0x00004238`.

Commander successfully extracted the application payload from this GBL, confirming the container is parseable by the vendor tool.

## Structural Zigbee OTA result

Commander wrapped the GBL as a Zigbee OTA image with the live header identity and a one-step outer version advance:

- manufacturer: `0x100B`;
- image type: `0x020C`;
- file version: `0x10003608`;
- stack version: `0x0002`;
- field control: `0`;
- header string: `UNSIGNED STRUCTURAL ONLY`;
- bytes: `304586`;
- SHA-256: `b6d783a1f4e278efac63fcdf1351c8f7637fc62c90769e1d02e174ca0d646884`;
- one tag `0x0000` containing the GBL.

Commander and the repo parser agree on the header and embedded GBL. `--require-target-match` succeeds because that option validates only outer live manufacturer/image/version targeting. It is **not** a deployment-safety approval.

## New hard gate: internal application version

Silicon Labs documents that the bootloader reads the application version from `ApplicationProperties_t` / `ApplicationData_t` inside the GBL. If application rollback protection is enabled, an upgrade is accepted only when that internal version is at least the highest version previously seen.

Sources:

- https://docs.silabs.com/mcu-bootloader/3.0.1/gecko-bootloader-api/application-properties
- https://docs.silabs.com/shared-content/latest/bootloader-user-guide-gsdk-4/09-gecko-bootloader-security-features
- https://docs.silabs.com/mcu-bootloader/latest/gecko-bootloader-api/common-interface

The installed stock bulb's **internal** ApplicationData version and rollback-protection policy are not remotely known. The Zigbee OTA outer file version `0x10003607` must not be copied into ApplicationData by assumption. Public reports also show outer `0x10003607` on unrelated Tuya products, supporting the conclusion that it is not proof of this bulb's internal bootloader version domain.

Therefore the current GBL with ApplicationData version `1` is format evidence only. Signing enforcement, encryption enforcement, rollback protection, stock internal application version, exact bootloader acceptance, and no-disassembly rollback all remain `UNRESOLVED`. No structural container may be indexed or offered to a bulb.