from dataclasses import dataclass
from datetime import datetime

from usb_whitelist_guard_core.domain.device import DeviceId


@dataclass(frozen=True, slots=True)
class AllowlistEntry:
    device_id: DeviceId
    added_at: datetime
    note: str | None = None

    def matches(self, device_id: DeviceId) -> bool:
        if (self.device_id.vid, self.device_id.pid) != (device_id.vid, device_id.pid):
            return False
        return (
            self.device_id.serial is None or self.device_id.serial == device_id.serial
        )
