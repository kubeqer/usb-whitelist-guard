import logging

logger = logging.getLogger(__name__)


class GuardError(Exception):
    """Base class for all usb-whitelist-guard errors."""

    def __init__(self, *args: object) -> None:
        super().__init__(*args)
        logger.debug("%s raised: %s", type(self).__name__, self)


class AllowlistUnavailableError(GuardError):
    """The allowlist could not be accessed (missing, corrupted, storage failure)."""


class DuplicateEntryError(GuardError):
    """An identical allowlist entry already exists."""


class EntryNotFoundError(GuardError):
    """The allowlist entry to remove does not exist."""


class EventStoreError(GuardError):
    """An event could not be stored or read."""


class DeviceBlockError(GuardError):
    """The operating system refused or failed to block a device."""
