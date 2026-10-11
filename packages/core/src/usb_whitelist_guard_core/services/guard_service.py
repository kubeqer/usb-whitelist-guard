import logging

from usb_whitelist_guard_core.domain import (
    Decision,
    DeviceBlockError,
    DeviceEvent,
    EventStoreError,
    UsbDevice,
)
from usb_whitelist_guard_core.policy import AccessPolicy
from usb_whitelist_guard_core.ports import DeviceBlocker, DeviceWatcher, EventSink
from usb_whitelist_guard_core.services.clock import Clock, utc_now

logger = logging.getLogger(__name__)


class GuardService:
    def __init__(
        self,
        watcher: DeviceWatcher,
        policy: AccessPolicy,
        blocker: DeviceBlocker,
        sink: EventSink,
        clock: Clock = utc_now,
    ) -> None:
        self._watcher = watcher
        self._policy = policy
        self._blocker = blocker
        self._sink = sink
        self._clock = clock

    def run(self) -> None:
        for device in self._watcher.watch():
            self.handle(device)

    def handle(self, device: UsbDevice) -> DeviceEvent:
        verdict = self._policy.evaluate(device)
        reason = verdict.reason

        if verdict.decision is Decision.BLOCK:
            try:
                self._blocker.block(device)
            except DeviceBlockError as exc:
                logger.error("Failed to block %s: %s", device.id, exc)
                reason = f"{reason}; block failed: {exc}"
        else:
            try:
                self._blocker.unblock(device)
            except DeviceBlockError as exc:
                logger.error("Failed to unblock %s: %s", device.id, exc)
                reason = f"{reason}; unblock failed: {exc}"

        event = DeviceEvent(self._clock(), device.id, verdict.decision, reason)
        logger.info("%s %s (%s): %s", verdict.decision, device.id, device.name, reason)
        try:
            self._sink.record(event)
        except EventStoreError:
            logger.exception("Failed to record event for %s", device.id)
        return event
