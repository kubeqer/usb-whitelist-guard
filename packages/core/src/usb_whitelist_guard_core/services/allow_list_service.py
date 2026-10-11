from collections.abc import Sequence

from usb_whitelist_guard_core.domain import AllowlistEntry, DeviceEvent, DeviceId
from usb_whitelist_guard_core.ports import AllowlistReader, AllowlistWriter, EventReader
from usb_whitelist_guard_core.services.clock import Clock, utc_now


class AllowlistService:
    def __init__(
        self,
        reader: AllowlistReader,
        writer: AllowlistWriter,
        events: EventReader,
        clock: Clock = utc_now,
    ) -> None:
        self._reader = reader
        self._writer = writer
        self._events = events
        self._clock = clock

    def list_entries(self) -> Sequence[AllowlistEntry]:
        return self._reader.list_all()

    def allow(self, device_id: DeviceId, note: str | None = None) -> AllowlistEntry:
        entry = AllowlistEntry(device_id, self._clock(), note)
        self._writer.add(entry)
        return entry

    def revoke(self, device_id: DeviceId) -> None:
        self._writer.remove(device_id)

    def recent_events(self, limit: int = 100) -> Sequence[DeviceEvent]:
        return self._events.recent(limit)
