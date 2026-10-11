import sys

from usb_whitelist_guard_core.ports import DeviceBlocker, DeviceWatcher


def create_platform_adapters() -> tuple[DeviceWatcher, DeviceBlocker]:
    if sys.platform == "win32":
        from usb_whitelist_guard_monitor.platforms.windows import (
            PnpDeviceBlocker,
            WmiDeviceWatcher,
        )

        return WmiDeviceWatcher(), PnpDeviceBlocker()
    if sys.platform == "linux":
        from usb_whitelist_guard_monitor.platforms.linux import (
            SysfsDeviceBlocker,
            UdevDeviceWatcher,
        )

        return UdevDeviceWatcher(), SysfsDeviceBlocker()
    raise RuntimeError(f"Unsupported platform: {sys.platform}")
