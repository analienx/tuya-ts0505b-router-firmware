# TS0505B OTA-first bring-up and recovery gates

This project is constrained to **non-destructive, no-disassembly development**. Installed bulbs are not to be opened. The intended deployment path is Zigbee OTA only; software work may proceed until an actual OTA write is the next step.

## Gate A — live non-mutating identity

Collect from the installed devices/coordinator without writing firmware:

- complete Zigbee Basic cluster attributes;
- node descriptor / logical type / MAC capabilities;
- endpoint and cluster descriptors;
- manual Zigbee2MQTT OTA *check* metadata;
- manufacturer code, image type and current OTA file version;
- management LQI/routing support and response status;
- current neighbor/route observations relevant to each bulb;
- current firmware version and any available Tuya OTA catalogue metadata.

A Zigbee2MQTT OTA `check` is allowed because it first requests metadata and does not initiate installation. An OTA `update`, `schedule`, downgrade, or custom firmware submission remains outside this gate.

## Gate B — platform and compatibility identity

Tuya's public TS0505B/ZSU evidence remains the primary family/platform reference: ZSU, EFR32MG21, router role, Extended Color Light/RGBCW application, and reference OTA identity `0x1002/0x1602`.

Live interrogation has now proved that the installed `_TZ3210_mja6r5ix` population uses a different OTA identity: `0x100B/0x020C`, file version `0x10003607`, field control `0`. target-a and target-b independently returned the same tuple.

Therefore:

- the live tuple is authoritative for candidate OTA targeting;
- `0x1002/0x1602` is reference-only and must not be forced onto the installed bulbs;
- the ZSU/EFR32MG21 platform hypothesis remains useful but is not yet binary-compatibility proof;
- compatibility stays `UNRESOLVED_IDENTITY_MISMATCH` until public/build artifact evidence explains the OEM tuple.

No powered-off teardown, PCB photography or debug-port identification is part of the plan.

## Gate C — OTA bootloader acceptance and recovery

Before the first candidate OTA, establish a recovery strategy that requires no bulb opening.

Required analysis:

1. identify whether the installed client responds to standard OTA query-next-image flows;
2. establish the live manufacturer code/image type/file version;
3. determine the expected Tuya UG/GBL/OTA container relationship from public tooling/source;
4. determine whether the existing Gecko Bootloader likely requires signed and/or encrypted GBL files;
5. never assume an unsigned custom image will install merely because the OTA cluster exists;
6. never test acceptance on more than one canary.

Silicon Labs treats signed/encrypted upgrade enforcement as configurable bootloader policy. Therefore the first write is an experiment at the bootloader policy boundary and must have explicit authorization.

Rollback priority:

- preferred: verified stock OTA image accepted by the same bootloader;
- acceptable for first canary only after review: candidate designed so bootloader rejects incompatible bytes before application replacement, with a clear stop condition if verification fails;
- unacceptable: any plan whose only recovery path is SWD/JTAG/opening the bulb.

## Gate D — RGB+CCT application compatibility

Tuya publishes a reference five-channel configuration:

- Red: PA3
- Green: PD2
- Blue: PC5
- Cold white: PA4
- Warm white: PA0

This is useful to build the reference-compatible application, but it is not treated as direct proof that every `_TZ3210_<PID>` production board is wired identically.

The build must preserve configurable:

- PWM enable/frequency/polarity;
- RGBCW channel selection;
- minimum/maximum duty cycles;
- RGB/CW power limits;
- CCT range;
- gamma/white balance;
- startup behavior;
- Tuya-specific command compatibility where required.

Before a canary is considered healthy, test each channel and mixed white/color modes at low/moderate output first. Any wrong channel, stuck output, flicker, thermal anomaly, or loss of off control is an immediate stop.

## Gate E — reproducible build-only candidate

Prefer the Tuya TS0505B/ZSU lighting application conventions for device identity and lighting behavior. Integrate the reviewed router profile without changing OTA identity or inventing a new endpoint model.

Required outputs:

- exact source SHA;
- pinned Tuya/Silicon Labs source/toolchain provenance;
- compile/link success;
- flash/RAM usage;
- application image plus Tuya-compatible UG/GBL/OTA artifact as available;
- SHA-256 of every candidate binary/container;
- parser output proving manufacturer code, image type and file version;
- structural checks for MG21 flash bounds and bootloader/application separation;
- CI policy validation.

Still no installed bulb mutation at this gate.

## Gate F — one-device OTA canary

Select exactly one bulb. Record:

- IEEE address and friendly name;
- live stock OTA tuple;
- physical location;
- baseline command timeout/routing metrics;
- stock software version;
- candidate source/artifact hashes;
- exact OTA request payload/index used;
- postflight functional/network checks;
- stop/rollback conditions.

The first `ota_update/update` request is the F2 mutation boundary and requires explicit authorization immediately before execution.

## Gate G — soak and expansion

Minimum canary soak: 24 hours. Preferred: 72 hours.

Acceptance requires:

- zero unexplained leaves/rejoins;
- no watchdog/reset regression;
- command success and latency better than or at least materially more stable than stock;
- no route/source-route pathology introduced;
- stable neighbor participation when the network chooses the bulb as a router;
- coordinator restart and bulb power-cycle recovery;
- correct on/off, brightness, color temperature and RGB behavior;
- no 1%/attribute desynchronization regression;
- no excessive broadcasts or many-to-one traffic originated by the bulb.

Only then consider target-b/3.

## Hard constraints

- No bulb disassembly.
- No SWD/JTAG/debug-pad recovery plan.
- No energized internal probing.
- No custom OTA upload before explicit authorization.
- No fleet rollout before a measured one-device canary.
