import tkinter as tk
from pathlib import Path
from tkinter import ttk

from usb_whitelist_guard_core.domain import DeviceId
from usb_whitelist_guard_core.services import AllowlistService

from usb_whitelist_guard_gui.allowlist_tab import AllowlistTab
from usb_whitelist_guard_gui.events_tab import EventsTab


class MainWindow(ttk.Frame):
    def __init__(self, root: tk.Tk, service: AllowlistService, database: Path) -> None:
        super().__init__(root)
        root.title("USB Whitelist Guard")
        root.geometry("820x480")
        root.minsize(600, 320)
        self.pack(fill="both", expand=True)

        self._status = tk.StringVar()
        self._notebook = ttk.Notebook(self)
        self._allowlist = AllowlistTab(self._notebook, service, self._status.set)
        self._events = EventsTab(
            self._notebook, service, self._allow_from_event, self._status.set
        )
        self._notebook.add(self._allowlist, text="Allowlist")
        self._notebook.add(self._events, text="Events")
        self._notebook.pack(fill="both", expand=True, padx=8, pady=(8, 0))

        status_bar = ttk.Frame(self, padding=(8, 4))
        status_bar.pack(fill="x")
        ttk.Label(status_bar, textvariable=self._status).pack(side="left")
        ttk.Label(status_bar, text=str(database), foreground="gray").pack(side="right")

        self._allowlist.refresh()
        self._events.refresh()

    def _allow_from_event(self, device_id: DeviceId) -> None:
        self._notebook.select(self._allowlist)
        self._allowlist.add(device_id)
