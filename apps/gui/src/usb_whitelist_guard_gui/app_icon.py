import ctypes
import logging
import sys
import tkinter as tk
from importlib.resources import files

logger = logging.getLogger(__name__)

APP_ID = "usb-whitelist-guard"
_SIZES = (16, 24, 32, 48, 64, 128, 256)


def prepare_process() -> None:
    if sys.platform != "win32":
        return
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_ID)
    except AttributeError, OSError:
        logger.debug("Cannot set the AppUserModelID", exc_info=True)


def set_app_icon(root: tk.Tk) -> None:
    icons = files(__package__) / "icons"
    try:
        images = [
            tk.PhotoImage(master=root, file=str(icons / f"icon-{size}.png"))
            for size in reversed(_SIZES)
        ]
    except tk.TclError:
        logger.warning("Cannot load the application icon", exc_info=True)
        return
    root.iconphoto(True, *images)
    root._app_icons = images
