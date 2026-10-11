from typing import Protocol

from usb_whitelist_guard_core.domain import UsbDevice


class DeviceBlocker(Protocol):
    def block(self, device: UsbDevice) -> None: ...

    def unblock(self, device: UsbDevice) -> None: ...
