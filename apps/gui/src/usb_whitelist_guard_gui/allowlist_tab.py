from collections.abc import Callable
from tkinter import messagebox, ttk

from usb_whitelist_guard_core.domain import AllowlistEntry, DeviceId, GuardError
from usb_whitelist_guard_core.services import AllowlistService

from usb_whitelist_guard_gui.entry_dialog import ask_entry
from usb_whitelist_guard_gui.formatting import format_time

_COLUMNS = {
    "vid": ("VID", 70),
    "pid": ("PID", 70),
    "serial": ("Serial", 200),
    "note": ("Note", 260),
    "added": ("Added", 150),
}


class AllowlistTab(ttk.Frame):
    def __init__(
        self,
        parent: ttk.Notebook,
        service: AllowlistService,
        on_status: Callable[[str], None],
    ) -> None:
        super().__init__(parent, padding=8)
        self._service = service
        self._on_status = on_status
        self._entries: dict[str, AllowlistEntry] = {}

        toolbar = ttk.Frame(self)
        toolbar.pack(fill="x", pady=(0, 6))
        ttk.Button(toolbar, text="Add...", command=self.add).pack(side="left")
        ttk.Button(toolbar, text="Remove", command=self._remove_selected).pack(
            side="left", padx=6
        )
        ttk.Button(toolbar, text="Refresh", command=self.refresh).pack(side="right")

        self._tree = ttk.Treeview(
            self, columns=list(_COLUMNS), show="headings", selectmode="browse"
        )
        for column, (heading, width) in _COLUMNS.items():
            self._tree.heading(column, text=heading)
            self._tree.column(column, width=width, anchor="w")
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self._tree.yview)
        self._tree.configure(yscrollcommand=scrollbar.set)
        self._tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self._tree.bind("<Delete>", lambda _event: self._remove_selected())

    def refresh(self) -> None:
        try:
            entries = self._service.list_entries()
        except GuardError as exc:
            self._on_status(f"Cannot load allowlist: {exc}")
            return
        self._tree.delete(*self._tree.get_children())
        self._entries.clear()
        for entry in entries:
            device_id = entry.device_id
            iid = self._tree.insert(
                "",
                "end",
                values=(
                    device_id.vid,
                    device_id.pid,
                    device_id.serial or "any",
                    entry.note or "",
                    format_time(entry.added_at),
                ),
            )
            self._entries[iid] = entry
        self._on_status(f"{len(entries)} allowed device(s)")

    def add(self, initial: DeviceId | None = None) -> None:
        result = ask_entry(self, initial)
        if result is None:
            return
        device_id, note = result
        try:
            self._service.allow(device_id, note)
        except GuardError as exc:
            messagebox.showerror("Cannot allow device", str(exc), parent=self)
            return
        self.refresh()

    def _remove_selected(self) -> None:
        selection = self._tree.selection()
        if not selection:
            return
        device_id = self._entries[selection[0]].device_id
        if not messagebox.askyesno(
            "Remove device", f"Remove {device_id} from the allowlist?", parent=self
        ):
            return
        try:
            self._service.revoke(device_id)
        except GuardError as exc:
            messagebox.showerror("Cannot remove device", str(exc), parent=self)
        self.refresh()
