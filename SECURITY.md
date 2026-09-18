# Security and device-safety policy

Please report repository security problems privately through GitHub's security reporting mechanism if available, rather than publishing credentials, device identifiers, signing material, or exploit details in an issue.

Do not submit private Zigbee IEEE addresses, Home Assistant tokens, Tuya credentials, Wi-Fi credentials, private keys, vendor signing keys, or proprietary SDK archives.

Firmware changes must preserve the fail-closed deployment model. A pull request must not silently set `deployment_ready=true`, authorize device mutation, weaken target matching, bypass bootloader checks, or publish a deployable OTA binary without the evidence required by `docs/FLASHABILITY.md`.

The project deliberately separates build/research work from the first persistent OTA mutation. Hardware on mains voltage must never be opened or probed while energized.
