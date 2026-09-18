# D0 validation-hold OTA mode

This mode exists to separate **stock-client download/verification acceptance** from **application activation** for the frozen TS0505B D0 candidate.

It is not read-only. A validation-hold run still transfers the OTA image and writes the bulb's OTA staging/storage area. Therefore it remains behind the explicit device-mutation authorization boundary.

## Why a hold is required

Current zigbee-herdsman normally responds to a successful OTA `UpgradeEndRequest` with `currentTime=0` and `upgradeTime=1`. That schedules activation almost immediately after a successful transfer.

The Zigbee OTA protocol also defines `upgradeTime=0xFFFFFFFF` as an indefinite wait for a later upgrade command. Silicon Labs' OTA client architecture separates download/verification from the later bootload callback, so this gives us a materially safer diagnostic step.

## Frozen scope

The repository patcher changes behavior only when all three values match the frozen D0 candidate:

- manufacturer code `0x100B`;
- image type `0x020C`;
- file version `0x10003608`.

Every other OTA keeps zigbee-herdsman's ordinary `upgradeTime=1` behavior.

Use:

```sh
python tools/patch_zigbee_herdsman_d0_hold.py <path-to-zigbee-herdsman/src/controller/model/device.ts>
python tools/patch_zigbee_herdsman_d0_hold.py <path> --apply
python tools/patch_zigbee_herdsman_d0_hold.py <path> --require-patched
python tools/patch_zigbee_herdsman_d0_hold.py <path> --revert
```

The patcher fails closed if the upstream activation site is missing, duplicated, or structurally different. `--apply` creates a sibling `.d0-hold.bak` and refuses to overwrite an existing backup.

## Upstream compatibility proof

Verified on 2026-09-18 against both the production dependency and current upstream:

- zigbee-herdsman `10.9.1`, tag `v10.9.1`, commit `0968f979d558874b17396c96b66382d4236bbdcd`;
- zigbee-herdsman `10.9.4`, commit `e9dcfb5c5967fb8b279c92e4fd0afe3173c06124`;
- both versions expose exactly one eligible `upgradeEndResponse` activation site;
- both have the same unpatched source SHA-256 (LF checkout): `c9e676dbebb9fb9baf38efdfb5357ea13b58676fc528549eccfb97d887c7ce2f`;
- both produce the same patched source SHA-256: `dd763b290f780d1212343a303a794da348472b305fd711b4e07d724411ff0a98`;
- `pnpm run build` (`tsc`) passes on both;
- Biome check on `src/controller/model/device.ts` passes with no fixes on both.

The live Zigbee2MQTT 2.14.0 bridge reports zigbee-herdsman 10.9.1, so the production dependency is covered by this proof. These hashes identify the upstream source file shape, not the packaged Home Assistant add-on filesystem.

## Authorized validation-hold sequence

Immediately before a live validation-hold experiment:

1. capture fresh target-a/target-b reachability, LQI, stock version and OTA tuple;
2. select one canary only; target-c is not eligible for the first canary;
3. re-run `tools/preflight_d0_candidate.py` against the exact OTA bytes;
4. prove the production zigbee-herdsman source/bundle contains the D0 hold behavior for the frozen tuple;
5. serve the OTA only through the explicitly targeted one-device request path;
6. transfer and wait for the client's `UpgradeEndRequest` result;
7. require success before concluding that the stock client/bootloader accepted verification;
8. return `upgradeTime=0xFFFFFFFF` and confirm the stock application remains running;
9. remove the OTA source/provider and record the result.

Do not send a later upgrade/activation command without a separate explicit authorization at that mutation boundary.
