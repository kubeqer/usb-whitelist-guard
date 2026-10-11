from typing import Protocol

from usb_whitelist_guard_core.domain import UsbDevice, Verdict


class AccessPolicy(Protocol):
    def evaluate(self, device: UsbDevice) -> Verdict: ...
