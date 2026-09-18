# Tuya TS0505B router-first replacement firmware

Research-grade replacement Zigbee firmware for Tuya RGB+CCT bulbs identified as `TS0505B` / `_TZ3210_mja6r5ix`, with two goals: preserve standards-compliant lighting behavior and improve router reliability on large Zigbee meshes.

## Current state

**Source/build quality: reproducible. Deployment quality: not yet canary-ready.**

The public tree contains a deterministic Silicon Labs EFR32MG21 family-reference build, conservative router tuning, a board-neutral RGB+CCT state layer, exact endpoint/cluster identity, OTA/GBL parsers, target safety checks, and a structurally valid Zigbee OTA packaging path.

Two independent devices reported the same live OTA identity:

- manufacturer code: `0x100B`
- image type: `0x020C`
- installed file version: `0x10003607`
- field control: `0`

Tuya's public TS0505B documentation instead uses generic reference identity `0x1002/0x1602`. The measured live tuple is authoritative for targeting; the generic tuple is reference-only.

## Router profile v0

- router / receiver-on-when-idle
- neighbor table: **26** (vendor baseline 16)
- route table: 16
- discovery table: 8
- address table: 12
- broadcast table: 15
- no concentrator role
- no periodic many-to-one originator behavior
- NVM/rejoin and OTA/recovery remain first-class surfaces

The neighbor-table increase costs 216 B of aligned BSS and is offset by a 216 B reduction in the generated managed heap, with no application BIN-size growth.

## Reproducible build evidence

Pinned structural baseline:

- Simplicity SDK 2026.6.1
- EmberZNet 9.1.1
- EFR32MG21A020F1024IM32 family-reference compile envelope
- SLC 6.0.23
- Arm GNU 14.2.1
- ZAP 2026.6.18

The exact endpoint-v0 structural BIN is 304440 bytes with SHA-256:

`b9cd57674051d9239489f639f017b5be112329743ce861ca9f84ae82ba573042`

Independent generation from the pinned vendor template reproduced the same bytes.

## What still blocks a flashable release

A syntactically valid OTA file is **not** sufficient. The remaining blockers are deliberately fail-closed:

- installed PCB/flash-layout compatibility is not independently proven
- production RGB+CCT PWM/electrical mapping is not yet verified
- stock Gecko Application Properties version is unknown
- bootloader rollback/signature/encryption policy is unresolved
- no verified stock rollback OTA exists
- no final candidate source/app/GBL/OTA hashes are frozen

Run:

```sh
python tools/verify_flashability_gate.py
```

for the exact current blocker list. See [docs/FLASHABILITY.md](docs/FLASHABILITY.md) for the release contract.

## Quality gate

The repository uses only Python standard-library tooling for its policy/format checks:

```sh
python tools/quality_gate.py
```

The public CI runs this on Linux and Windows. The stronger form:

```sh
python tools/quality_gate.py --require-flashable
```

must remain red until every deployment prerequisite is genuinely resolved.

## Safety and privacy

The public evidence uses aliases `target-a/b/c`; household Zigbee IEEE addresses and room-specific names are intentionally excluded. No vendor SDK trees, proprietary stock firmware, signing material, or deployable OTA/GBL/BIN files are committed.

The project is OTA-first and no-disassembly by design. No production device should be written until a one-device canary package satisfies the flashability contract and the operator explicitly authorizes the persistent OTA mutation.

## Repository map

- `firmware/` — target/build manifests and application overlay
- `tools/` — parsers, validators, reproducibility and quality gates
- `tests/` — host tests and parser/manifest regression coverage
- `evidence/` — sanitized empirical/build evidence
- `docs/FLASHABILITY.md` — definition of canary-ready
- `docs/ROUTER_POLICY.md` — routing design rationale
- `docs/CANARY_RUNBOOK.md` — one-device preflight/postflight/soak plan
- `PROJECT_STATUS.md` — detailed current engineering state

## License

Project-owned source and documentation are MIT licensed. Vendor SDKs and firmware are not redistributed; see [THIRD_PARTY.md](THIRD_PARTY.md).
