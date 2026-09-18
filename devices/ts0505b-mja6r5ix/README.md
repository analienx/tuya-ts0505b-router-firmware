# `_TZ3210_mja6r5ix` / TS0505B target ledger

Status: **OTA identity measured; platform strongly indicated; deployment contract incomplete**

## Sanitized installed population

| Public alias | Current role | Stock build | OTA evidence |
|---|---|---|---|
| `target-a` | Router | `z.1.0` / app 112 | directly measured |
| `target-b` | Router | `z.1.0` / app 112 | directly measured |
| `target-c` | Router | `z.1.0` / app 112 | inferred from identical fingerprint |

The public mirror intentionally omits household IEEE addresses. All three share `TS0505B`, `_TZ3210_mja6r5ix`, HA model `TS0505B_1_1`, stack 2, hardware 0, mains power, endpoint 1 Extended Color Light, and OTA/Time output clusters.

## Measured live OTA identity

Two independent devices emitted the same Query Next Image tuple:

- manufacturer `0x100B`
- image type `0x020C`
- current file version `0x10003607`
- field control `0`

This tuple is authoritative for candidate targeting.

## Platform evidence

Tuya's current TS0505B Lighting PDK identifies ZSU / EFR32MG21, with `EFR32MG21A020F1024IM32` primary and a documented 768 KiB alternative. The repository therefore uses MG21 as a structural compile envelope, not as proof of the exact production flash geometry.

## Remaining flashability unknowns

- exact production flash/bootloader/storage/NVM layout
- production RGB+CCT PWM pins, polarity, frequency, limits, and safe reset state
- stock Gecko Application Properties version
- bootloader upgrade-signature, encryption, and rollback-protection policy
- verified stock rollback image or reviewed reject-safe recovery classification
- final candidate source/app/GBL/OTA hashes and internal/outer version pair
- RF/TX-power ceiling for the exact module/board

See `docs/FLASHABILITY.md` and `python tools/verify_flashability_gate.py` for the machine-enforced release contract.
