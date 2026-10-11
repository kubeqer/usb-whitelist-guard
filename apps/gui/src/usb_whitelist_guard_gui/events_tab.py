from collections.abc import Callable
from tkinter import ttk

from usb_whitelist_guard_core.domain import Decision, DeviceEvent, DeviceId, GuardError
from usb_whitelist_guard_core.services import AllowlistService

from usb_whitelist_guard_gui.formatting import format_time

_COLUMNS = {
    "time": ("Time", 150),
    "device": ("Device", 230),
    "decision": ("Decision", 80),
    "reason": ("Reason", 300),
}
_REFRESH_MS = 2000
_LIMIT = 500


class EventsTab(ttk.Frame):
    def __init__(
        self,
        parent: ttk.Notebook,
        service: AllowlistService,
        on_allow: Callable[[DeviceId], None],
        on_status: Callable[[str], None],
    ) -> None:
        super().__init__(parent, padding=8)
        self._service = service
        self._on_allow = on_allow
        self._on_status = on_status
        self._events: dict[str, DeviceEvent] = {}
        self._shown: list[DeviceEvent] = []

        toolbar = ttk.Frame(self)
        toolbar.pack(fill="x", pady=(0, 6))
        ttk.Button(
            toolbar, text="Allow selected device…", command=self._allow_selected
        ).pack(side="left")
        ttk.Button(toolbar, text="Refresh", command=self.refresh).pack(side="right")

        self._tree = ttk.Treeview(
            self, columns=list(_COLUMNS), show="headings", selectmode="browse"
        )
        for column, (heading, width) in _COLUMNS.items():
            self._tree.heading(column, text=heading)
            self._tree.column(column, width=width, anchor="w")
        self._tree.tag_configure(Decision.BLOCK, foreground="#c0392b")
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self._tree.yview)
        self._tree.configure(yscrollcommand=scrollbar.set)
        self._tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self._tree.bind("<Double-1>", lambda _event: self._allow_selected())

        self.after(_REFRESH_MS, self._auto_refresh)

    def refresh(self) -> None:
        try:
            events = list(self._service.recent_events(_LIMIT))
        except GuardError as exc:
            self._on_status(f"Cannot load events: {exc}")
            return
        if events == self._shown:
            return
        selected = self._selected_event()
        self._tree.delete(*self._tree.get_children())
        self._events.clear()
        for event in events:
            iid = self._tree.insert(
                "",
                "end",
                values=(
                    format_time(event.timestamp),
                    str(event.device_id),
                    event.decision,
                    event.reason,
                ),
                tags=(event.decision,),
            )
            self._events[iid] = event
            if event == selected:
                self._tree.selection_set(iid)
        self._shown = events

    def _auto_refresh(self) -> None:
        self.refresh()
        self.after(_REFRESH_MS, self._auto_refresh)

    def _selected_event(self) -> DeviceEvent | None:
        selection = self._tree.selection()
        return self._events.get(selection[0]) if selection else None

    def _allow_selected(self) -> None:
        event = self._selected_event()
        if event is not None:
            self._on_allow(event.device_id)
