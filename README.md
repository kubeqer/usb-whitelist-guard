# usb-whitelist-guard
## Requirements

### Functional

- Detect newly connected USB devices in real time (Linux: udev, Windows: WMI).
- Read device VID/PID (and serial if available) and check it against an allowlist file.
- Automatically block unknown devices (Linux: sysfs authorized = 0, Windows: Disable-PnpDevice).
= Log each event with timestamp, device ID and decision.

### Non-functional

- Runs on Linux and Windows from one Python codebase.
- Requires root / administrator privileges.
- Fail-secure: if the allowlist is missing or invalid, unknown devices are blocked.