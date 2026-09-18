# Public evidence and privacy

The public repository uses aliases `target-a`, `target-b`, and `target-c` for the installed test population. Their Zigbee IEEE addresses are intentionally redacted.

This does not reduce technical reproducibility. The evidence needed for firmware targeting is the shared manufacturer/model fingerprint plus the device-originated OTA tuple. Exact household device addresses and room names are operational data, not firmware evidence.

The private development environment may retain the mapping required for a future one-device canary. It must not be copied into public issues, logs, fixtures, or release artifacts.
