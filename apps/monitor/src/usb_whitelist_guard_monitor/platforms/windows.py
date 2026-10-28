import re
import subprocess
from collections.abc import Iterator

import pythoncom
import wmi
from usb_whitelist_guard_core.domain import DeviceBlockError, DeviceId, UsbDevice

_CREATION_QUERY = (
    "SELECT * FROM __InstanceCreationEvent WITHIN 1 "
    "WHERE TargetInstance ISA 'Win32_PnPEntity' "
    r"AND TargetInstance.PNPDeviceID LIKE 'USB\\VID[_]%'"
)
_CONNECTED_QUERY = (
    "SELECT PNPDeviceID, Name FROM Win32_PnPEntity "
    r"WHERE PNPDeviceID LIKE 'USB\VID[_]%'"
)
_INSTANCE_ID = re.compile(
    r"^USB\\VID_([0-9A-F]{4})&PID_([0-9A-F]{4})\\(.+)$", re.IGNORECASE
)
_DISABLED_ERROR_CODE = 22
_POLL_MS = 1000
_POWERSHELL_TIMEOUT_S = 60


class WmiDeviceWatcher:
    def connected(self) -> Iterator[UsbDevice]:
        pythoncom.CoInitialize()
        try:
            devices = [
                to_usb_device(entity.PNPDeviceID, entity.Name)
                for entity in wmi.WMI().query(_CONNECTED_QUERY)
            ]
        finally:
            pythoncom.CoUninitialize()
        yield from (device for device in devices if device is not None)

    def watch(self) -> Iterator[UsbDevice]:
        pythoncom.CoInitialize()
        try:
            watcher = wmi.WMI().watch_for(raw_wql=_CREATION_QUERY)
            while True:
                try:
                    entity = watcher(timeout_ms=_POLL_MS)
                except wmi.x_wmi_timed_out:
                    continue
                device = to_usb_device(entity.PNPDeviceID, entity.Name)
                if device is not None:
                    yield device
        finally:
            pythoncom.CoUninitialize()


class PnpDeviceBlocker:
    def block(self, device: UsbDevice) -> None:
        instance_id = _quote(device.system_path)
        _run_powershell(f"Disable-PnpDevice -InstanceId {instance_id} -Confirm:$false")

    def unblock(self, device: UsbDevice) -> None:
        instance_id = _quote(device.system_path)
        _run_powershell(
            f"$device = Get-PnpDevice -InstanceId {instance_id}; "
            f"if ($device.ConfigManagerErrorCode -eq {_DISABLED_ERROR_CODE}) "
            f"{{ Enable-PnpDevice -InstanceId {instance_id} -Confirm:$false }}"
        )


def to_usb_device(instance_id: str, name: str | None = None) -> UsbDevice | None:
    device_id = parse_instance_id(instance_id)
    if device_id is None:
        return None
    return UsbDevice(device_id, instance_id, name)


def parse_instance_id(instance_id: str) -> DeviceId | None:
    match = _INSTANCE_ID.match(instance_id)
    if match is None:
        return None
    vid, pid, tail = match.groups()
    serial = None if "&" in tail else tail
    return DeviceId(vid, pid, serial)


def _quote(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def _run_powershell(script: str) -> None:
    command = [
        "powershell.exe",
        "-NoProfile",
        "-NonInteractive",
        "-Command",
        (
            f"$ErrorActionPreference = 'Stop'; try {{ {script} }} "
            "catch { [Console]::Error.WriteLine($_.Exception.Message); exit 1 }"
        ),
    ]
    try:
        result = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=_POWERSHELL_TIMEOUT_S,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise DeviceBlockError(f"PowerShell failed: {exc}") from exc
    if result.returncode != 0:
        raise DeviceBlockError(
            result.stderr.strip() or f"exit code {result.returncode}"
        )
