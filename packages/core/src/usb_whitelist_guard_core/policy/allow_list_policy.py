from usb_whitelist_guard_core.domain import UsbDevice, Verdict
from usb_whitelist_guard_core.ports import AllowlistReader


class AllowlistPolicy:
    def __init__(self, allowlist: AllowlistReader) -> None:
        self._allowlist = allowlist

    def evaluate(self, device: UsbDevice) -> Verdict:
        candidates = self._allowlist.candidates_for(device.id.vid, device.id.pid)
        if any(entry.matches(device.id) for entry in candidates):
            return Verdict.allow("on allowlist")
        return Verdict.block("not on allowlist")
