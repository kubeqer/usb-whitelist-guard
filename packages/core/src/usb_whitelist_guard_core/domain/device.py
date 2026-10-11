import re
from dataclasses import dataclass

_HEX4 = re.compile(r"^[0-9a-f]{4}$")


@dataclass(frozen=True, slots=True)
class DeviceId:
    vid: str
    pid: str
    serial: str | None = None

    def __post_init__(self) -> None:
        vid = self.vid.strip().lower()
        pid = self.pid.strip().lower()
        if not _HEX4.match(vid):
            raise ValueError(f"Invalid VID: {self.vid!r}")
        if not _HEX4.match(pid):
            raise ValueError(f"Invalid PID: {self.pid!r}")
        serial = self.serial.strip() if self.serial else None
        object.__setattr__(self, "vid", vid)
        object.__setattr__(self, "pid", pid)
        object.__setattr__(self, "serial", serial or None)

    def __str__(self) -> str:
        base = f"{self.vid}:{self.pid}"
        return f"{base}:{self.serial}" if self.serial else base


@dataclass(frozen=True, slots=True)
class UsbDevice:
    id: DeviceId
    system_path: str
    name: str | None = None
