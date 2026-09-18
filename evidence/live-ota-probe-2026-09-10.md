# Live OTA identity probe — 2026-09-10

## Scope and safety

Read-only Zigbee2MQTT OTA `check` interrogation of the installed `_TZ3210_mja6r5ix` / `TS0505B` bulbs. A temporary exact-fingerprint external converter enabled OTA metadata handling only; no firmware image was offered, transferred, scheduled, or installed.

After capture, the temporary converter was removed, Zigbee2MQTT logging was restored from `debug` to `info`, and the production add-on was restarted cleanly. No bulb firmware or persistent bulb state was changed.

## Decisive device-originated evidence

`target-a` (`IEEE_REDACTED_A`) emitted:

```text
[2026-09-10 11:29:11] debug: z2m: Received Zigbee message from 'target-a', type 'commandQueryNextImageRequest', cluster 'genOta', data '{"fieldControl":0,"fileVersion":268449287,"imageType":524,"manufacturerCode":4107}' from endpoint 1 with groupID 0
```

Decoded tuple:

- manufacturer code: `4107` / `0x100B`
- image type: `524` / `0x020C`
- installed file version: `268449287` / `0x10003607`
- field control: `0`
- OTA check result: completed; no newer indexed image was available

`target-b` (`IEEE_REDACTED_B`) independently emitted the same tuple:

```text
[2026-09-10 11:30:10] debug: z2m: Received Zigbee message from 'target-b', type 'commandQueryNextImageRequest', cluster 'genOta', data '{"fieldControl":0,"fileVersion":268449287,"imageType":524,"manufacturerCode":4107}' from endpoint 1 with groupID 0
```

This is a two-device replication of the installed OTA identity.

`target-c` (`IEEE_REDACTED_C`) did not emit a Query Next Image request during the probe window. Ordinary traffic from it remained visible, including `genTime` and `lightingColorCtrl` messages. Given its identical `TS0505B / _TZ3210_mja6r5ix / z.1.0 / app 112 / stack 2 / hw 0` fingerprint and two matching peer devices, the project treats target-c as the same production population and inherits `0x100B / 0x020C / 0x10003607` for targeting. This remains explicitly inferred evidence, not a direct OTA measurement; its timeout makes it unsuitable for the first canary.

## Conclusion

The installed population must **not** be targeted using Tuya's generic TS0505B reference tuple `0x1002 / 0x1602`. The measured production OTA identity is `0x100B / 0x020C`; current installed file version on the two responding units is `0x10003607`.

The generic Tuya ZSU/TS0505B material remains useful as platform and application-reference evidence, but its binary/bootloader compatibility with this OEM population is unresolved until the identity difference is explained.

Rollback remains `UNRESOLVED`; no exact trustworthy stock OTA artifact for `0x100B / 0x020C` and `_TZ3210_mja6r5ix` has yet been verified.
