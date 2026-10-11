from collections.abc import Sequence
from typing import Protocol

from usb_whitelist_guard_core.domain import DeviceEvent


class EventSink(Protocol):
    def record(self, event: DeviceEvent) -> None: ...


class EventReader(Protocol):
    def recent(self, limit: int = 100) -> Sequence[DeviceEvent]: ...
