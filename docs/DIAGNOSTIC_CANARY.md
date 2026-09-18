# Diagnostic canary design

This document defines the **first firmware shape we want to be capable of deploying**, not authorization to deploy it.

## Purpose

The first successful custom OTA should resolve unknowns rather than maximize features. It should preserve the known Zigbee endpoint contract, keep router-v0 conservative, retain OTA/rejoin surfaces, and expose enough runtime diagnostics to classify the production bootloader and reset behavior.

## D0 candidate requirements

- exact live outer OTA identity `0x100B/0x020C` and a deliberately advanced outer file version;
- internal Gecko Application Properties version chosen from evidence, never copied from the outer Zigbee version by assumption;
- no bootloader replacement and no bootloader-region writes;
- no NVM/token-region writes outside the vendor application's normal contract;
- standard endpoint 1 / Extended Color Light identity preserved;
- router-v0 only: neighbor 26; route 16; discovery 8; address 12; broadcast 15; no concentrator;
- OTA Upgrade client remains available after boot;
- reset reason, application version, stack version and useful stack counters exposed through a read-only diagnostic surface where feasible;
- watchdog/rejoin behavior deterministic and documented.

## Physical-output rule

The Tuya PDK channel mapping is **reference evidence only**. D0 must not energize RGB/CCT outputs from the reference profile unless independent production-board evidence resolves channel mapping, polarity, PWM frequency, limits and safe reset state.

If those electrical facts remain unresolved, the D0 candidate remains build-only. A dark-but-networked canary is not useful if installation itself cannot be proven recoverable.

## Bootloader evidence to resolve before D0

The release ledger must classify:

- stock Gecko Application Properties version;
- rollback-protection policy;
- upgrade-signature enforcement;
- upgrade-encryption enforcement;
- storage capability/layout used by OTA;
- candidate GBL signed/encrypted state;
- candidate program ranges against proven application/storage/NVM boundaries;
- behavior when the candidate is rejected before application replacement.

Silicon Labs exposes capability flags for GBL support, storage, enforced upgrade signature/encryption, and rollback protection. Those flags are useful only if they can be obtained from trustworthy stock/build evidence or a safely running diagnostic application; they must not be guessed from SDK defaults.

## Recovery threshold

Before any actual OTA request, one of these must be true:

1. a verified stock image with the exact production bootloader acceptance path exists; or
2. the existing bootloader is independently demonstrated to reject the candidate class before destructive replacement, and the review documents the exact failure/reboot behavior.

An interrupted application upgrade remains a separate risk and must be covered by the proven storage/bootloader layout.

## Promotion

Only after D0 passes the repository flashability gate and an explicitly authorized one-device canary may the project validate physical RGB/CCT output, router behavior and the 24–72 h soak defined in `docs/CANARY_RUNBOOK.md`.
