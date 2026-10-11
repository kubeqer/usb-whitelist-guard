from collections.abc import Iterator
from typing import Protocol

from usb_whitelist_guard_core.domain import UsbDevice


class DeviceWatcher(Protocol):
    def watch(self) -> Iterator[UsbDevice]: ...
