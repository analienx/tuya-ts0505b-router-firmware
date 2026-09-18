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

Verified on 2026-09-18 against zigbee-herdsman `10.9.4`, commit `e9dcfb5c5967fb8b279c92e4fd0afe3173c06124`:

- exactly one eligible `upgradeEndResponse` activation site found;
- unpatched source SHA-256 (LF checkout): `c9e676dbebb9fb9baf38efdfb5357ea13b58676fc528549eccfb97d887c7ce2f`;
- generated patched source SHA-256: `dd763b290f780d1212343a303a794da348472b305fd711b4e07d724411ff0a98`;
- `pnpm run build` (`tsc`) passes;
- Biome check on `src/controller/model/device.ts` passes with no fixes.

These hashes identify the upstream source file shape, not a production Home Assistant add-on build.

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
