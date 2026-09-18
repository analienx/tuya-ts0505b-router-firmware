# Stock firmware baseline — 2026-09-09

Source: live production Zigbee2MQTT logs on the Home Assistant host. No device mutation was performed while collecting this evidence.

## Target population

| Device | IEEE | Firmware |
|---|---|---|
| target-a | `IEEE_REDACTED_A` | `z.1.0`, app 112 |
| target-b | `IEEE_REDACTED_B` | `z.1.0`, app 112 |
| target-c | `IEEE_REDACTED_C` | `z.1.0`, app 112 |

All three are reported by Zigbee2MQTT as routers.

## Confirmed stock failures

During an ordinary production session on 2026-09-09, Zigbee2MQTT recorded the following 10-second ZCL timeouts:

1. **08:57:28 — target-c**: `genOnOff.read(["onOff"])` timed out after 10000 ms.
2. **08:57:33 — target-a**: `lightingColorCtrl.moveToColorTemp(...)` timed out after 10000 ms.
3. **08:57:38 — target-c**: a second `genOnOff.read(["onOff"])` timed out after 10000 ms.
4. **08:57:48 — target-c**: `lightingColorCtrl.moveToColorTemp(...)` timed out after 10000 ms.

This establishes a concrete application/reachability regression target for the replacement firmware.

## Link-quality context

The bulbs were not simply absent from the network. Around the same session their reported Zigbee2MQTT link-quality values varied substantially:

- target-a: observed roughly **56–132** in the sampled window;
- target-b: observed roughly **72–192**;
- target-c: observed roughly **72–164+**.

The health snapshots in this session reported `leave_count=0` and `network_address_changes=0` for the three bulbs. Therefore a candidate should not be judged only by LQI; command success, routing behaviour and recovery must be measured directly.

## Canary comparison requirements

For the stock-vs-candidate comparison, collect at least:

- ZCL command attempts, success count and timeout count;
- command latency distribution where measurable;
- leave/rejoin and network-address change counts;
- LQI distribution rather than a single value;
- coordinator route/source-route errors over the same window;
- neighbour/routing observations showing whether traffic is actually forwarded through the bulb;
- power-cycle and coordinator-restart recovery;
- RGB, CCT, level and on/off correctness.

Minimum candidate soak: 24 h. Preferred before expanding beyond one bulb: 72 h.

## Interpretation

The goal is not to make the reported LQI number larger. The goal is to eliminate unexplained application timeouts and make the bulb a predictable forwarding node without increasing broadcast or route-discovery pathology.
