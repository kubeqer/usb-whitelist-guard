import tkinter as tk
from tkinter import ttk

from usb_whitelist_guard_core.domain import DeviceId

from usb_whitelist_guard_gui.theme import error_color, style_window

type EntryInput = tuple[DeviceId, str | None]


class EntryDialog(tk.Toplevel):
    def __init__(self, parent: tk.Misc, initial: DeviceId | None = None) -> None:
        super().__init__(parent)
        self.title("Allow device")
        self.resizable(False, False)
        self.transient(parent.winfo_toplevel())
        self.result: EntryInput | None = None

        self._vid = tk.StringVar(value=initial.vid if initial else "")
        self._pid = tk.StringVar(value=initial.pid if initial else "")
        self._serial = tk.StringVar(value=(initial.serial or "") if initial else "")
        self._note = tk.StringVar()
        self._error = tk.StringVar()

        form = ttk.Frame(self, padding=12)
        form.grid(sticky="nsew")
        fields = [
            ("Vendor ID (VID)", self._vid),
            ("Product ID (PID)", self._pid),
            ("Serial (empty = any)", self._serial),
            ("Note", self._note),
        ]
        for row, (label, variable) in enumerate(fields):
            ttk.Label(form, text=label).grid(row=row, column=0, sticky="w", pady=2)
            entry = ttk.Entry(form, textvariable=variable, width=36)
            entry.grid(row=row, column=1, sticky="ew", pady=2, padx=(8, 0))
            if row == 0:
                entry.focus_set()

        ttk.Label(form, textvariable=self._error, foreground=error_color(self)).grid(
            row=len(fields), column=0, columnspan=2, sticky="w", pady=(6, 0)
        )
        buttons = ttk.Frame(form)
        buttons.grid(
            row=len(fields) + 1, column=0, columnspan=2, sticky="e", pady=(8, 0)
        )
        ttk.Button(buttons, text="Cancel", command=self.destroy).pack(side="right")
        ttk.Button(buttons, text="Allow", command=self._submit).pack(
            side="right", padx=(0, 6)
        )

        self.bind("<Return>", lambda _event: self._submit())
        self.bind("<Escape>", lambda _event: self.destroy())
        style_window(self)
        self.wait_visibility()
        self.grab_set()

    def _submit(self) -> None:
        try:
            device_id = DeviceId(self._vid.get(), self._pid.get(), self._serial.get())
        except ValueError as exc:
            self._error.set(str(exc))
            return
        self.result = (device_id, self._note.get().strip() or None)
        self.destroy()


def ask_entry(parent: tk.Misc, initial: DeviceId | None = None) -> EntryInput | None:
    dialog = EntryDialog(parent, initial)
    parent.wait_window(dialog)
    return dialog.result
