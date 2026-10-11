import argparse
import logging
import tkinter as tk
from pathlib import Path
from tkinter import messagebox

from usb_whitelist_guard_core.config import database_url, default_database_path
from usb_whitelist_guard_core.services import AllowlistService
from usb_whitelist_guard_core.storage import (
    SqlAllowlistRepository,
    SqlEventRepository,
    make_engine,
    make_session_factory,
    upgrade_schema,
)

from usb_whitelist_guard_gui.app_icon import APP_ID, prepare_process, set_app_icon
from usb_whitelist_guard_gui.main_window import MainWindow
from usb_whitelist_guard_gui.theme import THEMES, apply_theme

logger = logging.getLogger(__name__)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    logging.basicConfig(level=logging.INFO)

    prepare_process()
    root = tk.Tk(className=APP_ID)
    set_app_icon(root)
    try:
        service = _open_service(args.database)
    except Exception as exc:
        logger.exception("Cannot open database %s", args.database)
        root.withdraw()
        messagebox.showerror(
            "USB Whitelist Guard",
            f"Cannot open database {args.database}:\n\n{exc}\n\n"
            "Run as root / administrator, or pass --database.",
        )
        root.destroy()
        return 1

    apply_theme(root, args.theme)
    MainWindow(root, service)
    root.mainloop()
    return 0


def _open_service(database: Path) -> AllowlistService:
    database.parent.mkdir(parents=True, exist_ok=True)
    engine = make_engine(database_url(database))
    upgrade_schema(engine)
    sessions = make_session_factory(engine)
    allowlist = SqlAllowlistRepository(sessions)
    return AllowlistService(allowlist, allowlist, SqlEventRepository(sessions))


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="usb-whitelist-guard-gui")
    parser.add_argument("--database", type=Path, default=default_database_path())
    parser.add_argument("--theme", choices=THEMES, default="system")
    return parser.parse_args(argv)
