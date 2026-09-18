# Flashability contract

"Flashable" means more than "the project builds" or "the OTA header parses." A release is canary-ready only when every gate below is machine-verifiable and supported by evidence.

1. **Target identity:** live OTA manufacturer/image type/version are measured on at least two matching devices.
2. **Platform compatibility:** the installed module/SoC and memory layout are independently supported; family-reference evidence alone is insufficient.
3. **Board output:** RGB+CCT PWM pins, polarity, frequency, safe defaults, and power limits are verified for the production board.
4. **Bootloader contract:** stock Gecko Application Properties version plus rollback, signature, and encryption policy are resolved.
5. **Recovery:** either a verified stock rollback OTA exists or a reviewed bootloader-reject-safe recovery classification exists.
6. **Candidate freeze:** source SHA, application/GBL/OTA hashes, outer OTA version, internal GBL application version, signed/encrypted state, and flash ranges are frozen.
7. **Functional parity:** on/off, level, CT, HS/XY/RGB, groups/scenes, startup, rejoin, and OTA behavior pass the test matrix.
8. **Router policy:** router-v0 remains conservative, non-concentrator, reproducible, and within measured RAM/flash budget.

Run `python tools/verify_flashability_gate.py` to see current blockers. Run it with `--require-ready` only when preparing an explicitly authorized one-device OTA canary.

The repository must never claim canary readiness merely because a structurally valid OTA container exists.
