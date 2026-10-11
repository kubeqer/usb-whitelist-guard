from datetime import UTC, datetime

from usb_whitelist_guard_core.domain import (
    AllowlistEntry,
    Decision,
    DeviceEvent,
    DeviceId,
)
from usb_whitelist_guard_core.storage.models import AllowlistRow, EventRow


def entry_from_row(row: AllowlistRow) -> AllowlistEntry:
    return AllowlistEntry(
        device_id=DeviceId(row.vid, row.pid, row.serial),
        added_at=_as_utc(row.added_at),
        note=row.note,
    )


def entry_to_row(entry: AllowlistEntry) -> AllowlistRow:
    return AllowlistRow(
        vid=entry.device_id.vid,
        pid=entry.device_id.pid,
        serial=entry.device_id.serial,
        note=entry.note,
        added_at=entry.added_at,
    )


def event_from_row(row: EventRow) -> DeviceEvent:
    return DeviceEvent(
        timestamp=_as_utc(row.timestamp),
        device_id=DeviceId(row.vid, row.pid, row.serial),
        decision=Decision(row.decision),
        reason=row.reason,
    )


def event_to_row(event: DeviceEvent) -> EventRow:
    return EventRow(
        timestamp=event.timestamp,
        vid=event.device_id.vid,
        pid=event.device_id.pid,
        serial=event.device_id.serial,
        decision=event.decision.value,
        reason=event.reason,
    )


def _as_utc(value: datetime) -> datetime:
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value
