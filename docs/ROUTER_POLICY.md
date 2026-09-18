# Router policy

## Objective

Make the TS0505B a boring, standards-compliant, always-on Zigbee router that forwards traffic reliably in a dense production mesh while retaining correct RGB+CCT light behaviour.

## Stack baseline

Use Silicon Labs Simplicity SDK 2026.6.1 / EmberZNet 9.1.1 or a later version only after an explicit compatibility review. Pin the exact SDK/build inputs before producing a candidate artifact.

## Initial stack configuration

| Parameter | v0 value | Reason |
|---|---:|---|
| `SLI_ZIGBEE_PRIMARY_NETWORK_DEVICE_TYPE` | router | Mandatory role |
| `SL_ZIGBEE_NEIGHBOR_TABLE_SIZE` | **26** | Silicon Labs-supported maximum; improves the number of router neighbors tracked vs default 16 |
| `SL_ZIGBEE_ROUTE_TABLE_SIZE` | 16 | Keep vendor default until route-pressure evidence justifies a change |
| `SL_ZIGBEE_DISCOVERY_TABLE_SIZE` | 8 | Keep vendor default initially |
| `SL_ZIGBEE_ADDRESS_TABLE_SIZE` | 12 | Keep EmberZNet 9.1 default initially |
| `SL_ZIGBEE_BROADCAST_TABLE_SIZE` | 15 | Must remain conservative/network-compatible; do not increase casually |
| `SL_ZIGBEE_MAX_END_DEVICE_CHILDREN` | stack default | Do not invent unsupported child capacity |
| concentrator | disabled | Ordinary bulb routers should not originate periodic many-to-one route discovery |
| receiver on when idle | enabled | Mains router must remain continuously available |

The neighbor-table increase costs approximately 180 additional bytes of RAM relative to 16 entries (10 extra entries × 18 bytes/entry), which is a reasonable first trade if the exact part's memory budget confirms it.

## What "better router" means

A candidate is not better merely because it has larger tables. It must demonstrate:

1. **Stable participation** — stays attached and routable for the entire soak window; no unexplained leave/rejoin cycles.
2. **Forwarding usefulness** — coordinator topology shows real neighboring/child traffic using the bulb where topology makes that appropriate.
3. **No route pathology** — no increase in source-route failures, many-to-one failures, broadcast storms, or route-discovery churn attributable to the bulb.
4. **Management visibility** — responds correctly to standard management LQI/routing requests where the stack exposes them.
5. **Recovery behaviour** — survives coordinator restart and bulb power cycle; securely rejoins without factory reset.
6. **Application integrity** — On/Off, Level and Color commands remain responsive under routing load.
7. **No broadcast abuse** — no custom periodic network-wide traffic for the sake of appearing "active" as a router.

## Baseline and canary metrics

Capture before and after, over comparable windows:

- bulb availability and rejoin count;
- LQI/neighbor observations;
- coordinator route/source-route failures;
- route-discovery and many-to-one error counts;
- command latency and failed commands to the bulb;
- number of neighbors visible from the bulb, if available;
- evidence of other nodes routing through the bulb, if coordinator diagnostics expose it;
- heap/RAM headroom in the firmware build;
- reset reason/watchdog count.

A minimum useful canary soak is 24 h; a 72 h soak is preferred before expanding to all three bulbs.

## Non-goals

- turning every bulb into a concentrator;
- raising broadcast limits;
- using maximum transmit power without RF evidence/regulatory review;
- accepting a larger table merely because RAM exists;
- changing Zigbee network security semantics;
- sacrificing normal light compatibility for proprietary telemetry.

## Expansion rule

Only one installed bulb is flashed first. The remaining two are eligible only after the canary meets the functional and routing acceptance criteria and rollback remains verified.