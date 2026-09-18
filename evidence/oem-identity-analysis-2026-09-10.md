# OEM OTA identity analysis — 2026-09-10

## Measured installed identity

Two installed `_TZ3210_mja6r5ix` / `TS0505B` bulbs independently emitted the same Zigbee OTA Query Next Image tuple:

- manufacturer code `0x100B` (`4107`)
- image type `0x020C` (`524`)
- file version `0x10003607` (`268449287`)
- field control `0`

The same production population also reports node-descriptor / Zigbee manufacturer ID `4107` (`0x100B`). This is therefore not merely an OTA-parser interpretation.

## Independent public corroboration

An OpenHAB fingerprint posted in 2024 for the exact `_TZ3210_mja6r5ix` / `TS0505B` family reports:

- `zigbee_manufacturercode=0x100b`
- `firmwareVersion=0x10003607`
- app version 112 / `z.1.0`
- router / receiver-on-when-idle

Source: https://community.openhab.org/t/zigbee-bulb-not-changing-colors/156269

This strongly corroborates that `0x100B` and `0x10003607` are stable properties of this exact Tuya PID family, not corruption in our three-device network.

## Meaning of manufacturer code 0x100B

`0x100B` is assigned to Philips/Signify in Zigbee ecosystems; current CSA records also identify Signify Netherlands B.V. with vendor ID `0x100B`.

Reference: https://csa-iot.org/csa_product/philips-hue-bridge/

That does **not** prove these Tuya bulbs contain Philips/Signify firmware or are compatible with Hue OTA images. The Basic-cluster manufacturer string remains `_TZ3210_mja6r5ix`, and the product is publicly identified as Tuya TS0505B. The defensible interpretation is that this OEM firmware uses the `0x100B` numeric manufacturer code, intentionally or historically, despite the Tuya product identity.

## Image type 0x020C

No trustworthy public source found in this search ties the exact `0x100B/0x020C` pair to `_TZ3210_mja6r5ix`, nor was an exact `100B-020C` artifact present in the current `zigpy/zigpy-ota` repository tree/search.

Therefore `0x020C` remains an observed exact-device image type, not evidence of Signify/Hue binary compatibility.

## Safety consequence

Do not use a Signify/Hue firmware image merely because it shares manufacturer code `0x100B`, and do not rewrite a generic Tuya `0x1002/0x1602` image header to force acceptance. Either action could create a structurally valid but electrically/application-incompatible update.

Any future deployment candidate must satisfy **both**:

1. exact live OTA targeting identity `0x100B/0x020C` with a deliberate version greater than `0x10003607`; and
2. independently proven TS0505B/ZSU/MG21 application, bootloader, flash-layout and RGB+CCT compatibility.
