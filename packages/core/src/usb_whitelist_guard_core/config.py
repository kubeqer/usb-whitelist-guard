import os
import sys
from pathlib import Path

DATABASE_ENV = "USB_WHITELIST_GUARD_DB"


def default_database_path() -> Path:
    override = os.environ.get(DATABASE_ENV)
    if override:
        return Path(override)
    if sys.platform == "win32":
        program_data = Path(os.environ.get("PROGRAMDATA", r"C:\ProgramData"))
        return program_data / "usb-whitelist-guard" / "guard.db"
    return Path("/var/lib/usb-whitelist-guard/guard.db")


def database_url(path: Path) -> str:
    return f"sqlite:///{path.as_posix()}"
