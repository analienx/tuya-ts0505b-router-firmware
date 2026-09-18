# D0 flash-layout verification — 2026-09-18

Scope: offline/read-only verification of the frozen `d0.1-noled` diagnostic canary. No Home Assistant, Zigbee2MQTT, or bulb mutation was performed.

## Frozen identity

- OTA SHA-256: `55d976078d573aa4dd8833d8af0f000aacbdbef9850bb1e65e1ffe8c4816c549`
- OTA size: 304602 bytes
- GBL SHA-256: `eb7332f0576698f4e012e01e8a62e618e8be22174a9c76a482da9c162645b26b`
- GBL size: 304540 bytes
- application BIN SHA-256: `a5a0e1d49ca5224894059b999e35b5fa3e0c6f34ac657f72d8787117a7acf0d7`
- application BIN size: 304456 bytes
- OTA identity: `0x100B / 0x020C / 0x10003608`
- GBL Application Properties version: 1
- GBL signed: false
- GBL encrypted: false

Commander 1v24p3b1989 and an independent parser both reconfirmed the OTA container identity.

## GBL tag semantics and exact writes

Silicon Labs SDK source identifies tag `0xFD0303FD` as ERASEPROG, not legacy LZMA. ERASEPROG uses the same programming-address parser as plain PROG and carries uncompressed program bytes.

The complete GBL tag sequence is:

`HEADER -> APPLICATION -> ERASEPROG -> ERASEPROG -> END`

There are no bootloader-upgrade, SE-upgrade, encrypted-data, certificate, signature, delta, LZ4, or LZMA payload tags.

Exact programmed ranges:

- `0x00004000 .. 0x00004234` — 564 bytes
- `0x00004238 .. 0x0004E548` — 303888 bytes

Both ranges are byte-identical to the application BIN and to the S37 records. The four-byte `0x4234..0x4237` gap is linker alignment padding between the RAM-function load image and `.text`.

## Safety result

- no write targets an address below `0x4000`;
- the main bootloader region `0x0000..0x3FFF` is not part of the GBL payload;
- the highest page erased by the candidate ends at `0x50000`;
- `0x50000` is below the conservative 768-KiB ceiling `0xC0000`;
- the reference 1-MiB build places NVM3 at `0xF6000..0xFDFFF`, far above the candidate writes;
- the GBL end-tag integrity residue reproduces Silicon Labs' expected `0xDEBB20E3`.

Result: **PASS_FLASH_LAYOUT_ONLY**.

This does not prove that the installed production bootloader accepts unsigned/unencrypted Application Properties version 1, nor does it prove rollback/recovery behavior. Those remain explicit mutation-gate blockers.

The frozen metadata is recorded in `firmware/canary_d0_manifest.json`; `tools/preflight_d0_candidate.py` rechecks the actual OTA bytes before staging.
