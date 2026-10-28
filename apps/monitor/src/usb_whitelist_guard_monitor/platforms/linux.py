import logging
from collections.abc import Iterator
from pathlib import Path

import pyudev
from usb_whitelist_guard_core.domain import DeviceBlockError, DeviceId, UsbDevice

logger = logging.getLogger(__name__)


class UdevDeviceWatcher:
    def __init__(self, context: pyudev.Context | None = None) -> None:
        self._context = context or pyudev.Context()

    def connected(self) -> Iterator[UsbDevice]:
        udev_devices = self._context.list_devices(subsystem="usb", DEVTYPE="usb_device")
        for udev_device in udev_devices:
            if udev_device.sys_name.startswith("usb"):
                continue
            device = to_usb_device(udev_device)
            if device is not None:
                yield device

    def watch(self) -> Iterator[UsbDevice]:
        monitor = pyudev.Monitor.from_netlink(self._context)
        monitor.filter_by(subsystem="usb", device_type="usb_device")
        for udev_device in iter(monitor.poll, None):
            if udev_device.action != "add":
                continue
            device = to_usb_device(udev_device)
            if device is not None:
                yield device


class SysfsDeviceBlocker:
    def block(self, device: UsbDevice) -> None:
        _write_authorized(device, "0")

    def unblock(self, device: UsbDevice) -> None:
        if _read_authorized(device) == "0":
            _write_authorized(device, "1")


def to_usb_device(udev_device: pyudev.Device) -> UsbDevice | None:
    vid = _attribute(udev_device, "idVendor")
    pid = _attribute(udev_device, "idProduct")
    try:
        device_id = DeviceId(vid or "", pid or "", _attribute(udev_device, "serial"))
    except ValueError:
        logger.error("Cannot identify USB device at %s", udev_device.sys_path)
        return None
    return UsbDevice(
        device_id, udev_device.sys_path, _attribute(udev_device, "product")
    )


def _attribute(udev_device: pyudev.Device, name: str) -> str | None:
    try:
        return udev_device.attributes.asstring(name).strip() or None
    except KeyError, UnicodeDecodeError:
        return None


def _authorized_path(device: UsbDevice) -> Path:
    return Path(device.system_path) / "authorized"


def _read_authorized(device: UsbDevice) -> str:
    path = _authorized_path(device)
    try:
        return path.read_text().strip()
    except OSError as exc:
        raise DeviceBlockError(f"Cannot read {path}: {exc}") from exc


def _write_authorized(device: UsbDevice, value: str) -> None:
    path = _authorized_path(device)
    try:
        path.write_text(value)
    except OSError as exc:
        raise DeviceBlockError(f"Cannot write {path}: {exc}") from exc
