# Exact stock rollback search — 2026-09-10

## Target

- model: `TS0505B`
- exact manufacturer/PID: `_TZ3210_mja6r5ix`
- stock Basic cluster build: `z.1.0`
- app version: 112
- measured installed OTA identity: manufacturer `0x100B`, image type `0x020C`, file version `0x10003607` (target-a + target-b)
- generic Tuya family reference `0x1002/0x1602` is reference-only and is not a valid rollback-target identity for these installed bulbs

## Result

**No exact, trustworthy stock firmware artifact was located. Rollback remains `UNRESOLVED`.**

A follow-up search using the measured `0x100B/0x020C/0x10003607` identity also found no exact stock artifact. `0x100B` is associated with Philips/Signify, but independent public fingerprints show this exact Tuya PID itself uses that numeric manufacturer code. This is not permission to substitute a Hue image; see `evidence/oem-identity-analysis-2026-09-10.md`.

The search included:

- exact manufacturer string `_TZ3210_mja6r5ix`;
- exact PID suffix `mja6r5ix`;
- `TS0505B` with OTA/bin/UG/GBL/firmware terms;
- `TS0505B` with decimal/hex Tuya family OTA identity candidates;
- public GitHub code/results and Koenkk Zigbee OTA sources;
- public issue/discussion attachments and device reports.

## What was found

Public reports confirm the exact `_TZ3210_mja6r5ix` / `TS0505B_1_1` / `z.1.0` population is active in 2026 and exhibits reliability/application-state problems. These reports are useful as behavioral evidence but do not include a verified stock firmware binary.

Other `TS0505B` manufacturer/PID variants exist and some share similar cluster layouts. They are **not** acceptable rollback artifacts merely because the model ID matches.

## Acceptance rule for any future stock candidate

Do not promote a discovered image to `VERIFIED` rollback unless all relevant evidence aligns:

1. source provenance is trustworthy;
2. Zigbee OTA manufacturer code matches the live canary;
3. image type matches the live canary;
4. file/hardware version constraints are compatible;
5. model/PID or other authoritative evidence establishes compatibility with `_TZ3210_mja6r5ix`;
6. artifact parses correctly as Zigbee OTA/GBL where applicable;
7. SHA-256 is recorded;
8. delivery through the existing bootloader is technically supported.

A binary for `_TZ3210_it1u8ahz`, `_TZ3210_rcggc0ys`, `_TZ3210_pdqu9pot`, `_TZ3210_pwauw3g2` or another TS0505B variant is evidence/reference material, not rollback.

## Consequence for first canary

Because disassembly/SWD recovery is prohibited and verified stock bytes are absent, successful installation of a bad custom application could be unrecoverable if it prevents future OTA operation.

Therefore the first custom OTA cannot be represented as rollback-safe today. The final pre-F2 decision must state one of:

- `VERIFIED` — exact stock recovery path found and validated;
- `BOOTLOADER-REJECT-SAFE ONLY` — confidence is limited to rejection-before-swap for an invalid candidate, not recovery after a successfully installed bad application;
- `UNRESOLVED` — no practical no-disassembly rollback.

Current classification: **UNRESOLVED**.
