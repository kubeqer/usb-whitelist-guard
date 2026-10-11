from collections.abc import Sequence
from typing import Protocol

from usb_whitelist_guard_core.domain import AllowlistEntry, DeviceId


class AllowlistReader(Protocol):
    def candidates_for(self, vid: str, pid: str) -> Sequence[AllowlistEntry]: ...

    def list_all(self) -> Sequence[AllowlistEntry]: ...


class AllowlistWriter(Protocol):
    def add(self, entry: AllowlistEntry) -> None: ...

    def remove(self, device_id: DeviceId) -> None: ...
