import logging
from collections.abc import Iterable

from usb_whitelist_guard_core.domain import (
    AllowlistEntry,
    DuplicateEntryError,
    UsbDevice,
)
from usb_whitelist_guard_core.ports import AllowlistReader, AllowlistWriter, EventReader
from usb_whitelist_guard_core.services.clock import Clock, utc_now

logger = logging.getLogger(__name__)

FIRST_RUN_NOTE = "connected at first run"


def is_first_run(allowlist: AllowlistReader, events: EventReader) -> bool:
    return not allowlist.list_all() and not events.recent(limit=1)


def allow_connected_devices(
    devices: Iterable[UsbDevice],
    writer: AllowlistWriter,
    clock: Clock = utc_now,
) -> list[AllowlistEntry]:
    added = []
    for device in devices:
        entry = AllowlistEntry(device.id, clock(), _note(device))
        try:
            writer.add(entry)
        except DuplicateEntryError:
            continue
        logger.info("Allowed %s (%s): %s", device.id, device.name, FIRST_RUN_NOTE)
        added.append(entry)
    return added


def _note(device: UsbDevice) -> str:
    return f"{device.name} ({FIRST_RUN_NOTE})" if device.name else FIRST_RUN_NOTE
