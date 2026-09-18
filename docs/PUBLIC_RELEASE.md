# Public release model

The private engineering repository is the operational source of truth. Public releases are published from a privacy-sanitized snapshot so household device identifiers and old operational history are not exposed.

A public snapshot must pass `python tools/quality_gate.py` and `python tools/verify_public_hygiene.py`. It must not contain vendor SDK trees, proprietary firmware, private device identifiers, credentials, machine-specific user paths, or deployable firmware binaries.

Until the flashability contract is complete, public releases are source/research releases only. GitHub release assets must not include OTA/GBL/BIN firmware marked or implied as production-ready.

When the contract is eventually satisfied, the release process should publish source, reproducibility metadata, SHA-256 values, and a canary-specific artifact only after an explicit review of the exact candidate.
