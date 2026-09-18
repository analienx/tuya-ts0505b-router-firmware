# Contributing

Start with `README.md`, `docs/FLASHABILITY.md`, `docs/ROUTER_POLICY.md`, and `AGENTS.md`.

Use a topic branch and keep changes evidence-driven. Router settings must include a reason, memory impact, and test. Do not increase Zigbee tables wholesale.

Before opening a pull request, run:

```sh
python tools/quality_gate.py
```

A release candidate may additionally be checked with:

```sh
python tools/quality_gate.py --require-flashable
```

The second command is expected to fail until every deployment blocker is resolved and a candidate artifact is frozen.

Do not commit vendor SDK trees, proprietary firmware, generated deployable OTA/GBL/BIN files, credentials, private device identifiers, or machine-specific paths. See `THIRD_PARTY.md` and `SECURITY.md`.
