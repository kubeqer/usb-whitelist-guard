import ctypes
import logging
import sys
import tkinter as tk
from tkinter import font

import darkdetect
import sv_ttk

logger = logging.getLogger(__name__)

THEMES = ("system", "light", "dark")

_LINUX_FAMILIES = (
    "Noto Sans",
    "Cantarell",
    "Ubuntu",
    "DejaVu Sans",
    "Liberation Sans",
)
_TK_FONTS = (
    "TkDefaultFont",
    "TkTextFont",
    "TkMenuFont",
    "TkHeadingFont",
    "TkCaptionFont",
    "TkTooltipFont",
)
_SV_FONTS = {
    "SunValleyCaptionFont": "normal",
    "SunValleyBodyFont": "normal",
    "SunValleyBodyStrongFont": "bold",
    "SunValleyBodyLargeFont": "normal",
    "SunValleySubtitleFont": "bold",
    "SunValleyTitleFont": "bold",
    "SunValleyTitleLargeFont": "bold",
    "SunValleyDisplayFont": "bold",
}
_ERROR_COLORS = {"light": "#c0392b", "dark": "#ff6b6b"}
_DWMWA_USE_IMMERSIVE_DARK_MODE = 20


def apply_theme(root: tk.Tk, theme: str = "system") -> str:
    mode = _resolve(theme)
    sv_ttk.set_theme(mode, root)
    root.tk.call("configure_colors")
    if sys.platform == "win32":
        _windows_fonts(root)
    elif sys.platform != "darwin":
        _replace_fonts(root, _pick_family(root, _LINUX_FAMILIES))
    style_window(root)
    return mode


def error_color(root: tk.Misc) -> str:
    return _ERROR_COLORS[sv_ttk.get_theme(_root_of(root))]


def style_window(window: tk.Tk | tk.Toplevel) -> None:
    if sys.platform != "win32":
        return
    dark = ctypes.c_int(sv_ttk.get_theme(_root_of(window)) == "dark")
    try:
        window.update_idletasks()
        hwnd = ctypes.windll.user32.GetParent(window.winfo_id())
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd,
            _DWMWA_USE_IMMERSIVE_DARK_MODE,
            ctypes.byref(dark),
            ctypes.sizeof(dark),
        )
    except AttributeError, OSError:
        logger.debug("Cannot style the window title bar", exc_info=True)


def _resolve(theme: str) -> str:
    if theme != "system":
        return theme
    try:
        detected = darkdetect.theme()
    except Exception:
        logger.debug("Cannot detect the system theme", exc_info=True)
        detected = None
    return "dark" if detected == "Dark" else "light"


def _windows_fonts(root: tk.Tk) -> None:
    if "Segoe UI Variable Text" not in font.families(root):
        _replace_fonts(root, "Segoe UI")


def _replace_fonts(root: tk.Tk, family: str) -> None:
    for name, weight in _SV_FONTS.items():
        _configure(root, name, family=family, weight=weight)
    body_size = font.nametofont("SunValleyBodyFont", root).cget("size")
    for name in _TK_FONTS:
        _configure(root, name, family=family, size=body_size)


def _configure(root: tk.Tk, name: str, **options: object) -> None:
    try:
        font.nametofont(name, root).configure(**options)
    except tk.TclError:
        logger.debug("Font %s does not exist", name)


def _pick_family(root: tk.Tk, preferred: tuple[str, ...]) -> str:
    available = set(font.families(root))
    for family in preferred:
        if family in available:
            return family
    return font.nametofont("TkDefaultFont", root).actual("family")


def _root_of(window: tk.Misc) -> tk.Tk:
    return window._root()
