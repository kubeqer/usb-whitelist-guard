import logging

from usb_whitelist_guard_core.domain import UsbDevice, Verdict
from usb_whitelist_guard_core.policy.access_policy import AccessPolicy

logger = logging.getLogger(__name__)


class FailSecurePolicy:
    def __init__(self, inner: AccessPolicy) -> None:
        self._inner = inner

    def evaluate(self, device: UsbDevice) -> Verdict:
        try:
            return self._inner.evaluate(device)
        except Exception as exc:
            logger.exception("Policy failed for %s, blocking", device.id)
            return Verdict.block(f"policy error: {exc}")
