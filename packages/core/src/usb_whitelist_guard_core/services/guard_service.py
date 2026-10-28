import logging
import threading

from usb_whitelist_guard_core.domain import (
    Decision,
    DeviceBlockError,
    DeviceEvent,
    EventStoreError,
    UsbDevice,
    Verdict,
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
        self._lock = threading.Lock()
        self._decisions: dict[str, Decision] = {}
        self._failed: set[str] = set()

    def run(self) -> None:
        for device in self._watcher.watch():
            self.handle(device)

    def handle(self, device: UsbDevice) -> DeviceEvent:
        with self._lock:
            return self._apply(device, self._policy.evaluate(device))

    def has_failures(self) -> bool:
        with self._lock:
            return bool(self._failed)

    def reconcile(self) -> list[DeviceEvent]:
        devices = list(self._watcher.connected())
        events = []
        for device in devices:
            with self._lock:
                verdict = self._policy.evaluate(device)
                if self._decisions.get(device.system_path) is verdict.decision:
                    continue
                events.append(self._apply(device, verdict))
        connected = {device.system_path for device in devices}
        with self._lock:
            for path in self._decisions.keys() - connected:
                del self._decisions[path]
            self._failed &= connected
        return events

    def _apply(self, device: UsbDevice, verdict: Verdict) -> DeviceEvent:
        reason = verdict.reason
        self._decisions.pop(device.system_path, None)
        self._failed.add(device.system_path)

        if verdict.decision is Decision.BLOCK:
            try:
                self._blocker.block(device)
                self._decisions[device.system_path] = verdict.decision
                self._failed.discard(device.system_path)
            except DeviceBlockError as exc:
                logger.error("Failed to block %s: %s", device.id, exc)
                reason = f"{reason}; block failed: {exc}"
        else:
            try:
                self._blocker.unblock(device)
                self._decisions[device.system_path] = verdict.decision
                self._failed.discard(device.system_path)
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
