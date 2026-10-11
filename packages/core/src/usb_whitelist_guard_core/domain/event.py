from dataclasses import dataclass
from datetime import datetime

from usb_whitelist_guard_core.domain.decision import Decision
from usb_whitelist_guard_core.domain.device import DeviceId


@dataclass(frozen=True, slots=True)
class DeviceEvent:
    timestamp: datetime
    device_id: DeviceId
    decision: Decision
    reason: str
