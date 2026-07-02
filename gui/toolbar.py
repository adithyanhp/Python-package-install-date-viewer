"""
gui/toolbar.py

Top toolbar: search box, sort dropdown, refresh/export/install buttons.
"""

from __future__ import annotations

from typing import Callable

import customtkinter as ctk

from gui import theme

SORT_OPTIONS = (
    "Name (A-Z)",
    "Name (Z-A)",
    "Version",
    "Size (Largest)",
    "Size (Smallest)",
)


class Toolbar(ctk.CTkFrame):
    """Search, sort, and action buttons for the package table."""

    def __init__(
        self,
        master: ctk.CTkBaseClass,
        on_search: Callable[[str], None],
        on_sort_change: Callable[[str], None],
        on_refresh: Callable[[], None],
        on_export: Callable[[str], None],
        on_install: Callable[[str], None],
        **kwargs,
    ) -> None:
        super().__init__(master, corner_radius=0, fg_color=theme.BG_SECONDARY, **kwargs)
        self._on_search = on_search
        self._on_sort_change = on_sort_change
        self._on_refresh = on_refresh
        self._on_export = on_export
        self._on_install = on_install

        self.grid_columnconfigure(1, weight=1)

        self._search_var = ctk.StringVar()
        self._search_var.trace_add("write", self._handle_search)
        self._search_entry = ctk.CTkEntry(
            self,
            textvariable=self._search_var,
            placeholder_text="🔍  Search packages...",
            height=36,
            width=260,
        )
        self._search_entry.grid(row=0, column=0, sticky="w", padx=(16, 8), pady=12)

        self._sort_menu = ctk.CTkOptionMenu(
            self,
            values=list(SORT_OPTIONS),
            command=self._on_sort_change,
            height=36,
            width=170,
            fg_color=theme.BG_CARD,
            button_color=theme.ACCENT_DARK,
            button_hover_color=theme.ACCENT_HOVER,
        )
        self._sort_menu.grid(row=0, column=2, sticky="e", padx=8, pady=12)

        self._install_entry = ctk.CTkEntry(
            self,
            placeholder_text="Install package (e.g. requests==2.31.0)",
            height=36,
            width=260,
        )
        self._install_entry.grid(row=0, column=3, sticky="e", padx=8, pady=12)
        self._install_entry.bind("<Return>", self._handle_install_enter)

        self._install_btn = ctk.CTkButton(
            self,
            text="＋ Install",
            command=self._handle_install,
            height=36,
            width=90,
            fg_color=theme.SUCCESS,
            hover_color="#3BC46E",
            text_color="#0B1F14",
        )
        self._install_btn.grid(row=0, column=4, sticky="e", padx=8, pady=12)

        self._export_menu = ctk.CTkOptionMenu(
            self,
            values=["Export ▾", "Export CSV", "Export Excel", "Export PDF"],
            command=self._handle_export,
            height=36,
            width=130,
            fg_color=theme.BG_CARD,
            button_color=theme.ACCENT_DARK,
            button_hover_color=theme.ACCENT_HOVER,
        )
        self._export_menu.set("Export ▾")
        self._export_menu.grid(row=0, column=5, sticky="e", padx=8, pady=12)

        self._refresh_btn = ctk.CTkButton(
            self,
            text="⟳ Refresh",
            command=self._on_refresh,
            height=36,
            width=100,
            fg_color=theme.ACCENT_DARK,
            hover_color=theme.ACCENT_HOVER,
        )
        self._refresh_btn.grid(row=0, column=6, sticky="e", padx=(8, 16), pady=12)

    def _handle_search(self, *_args) -> None:
        self._on_search(self._search_var.get())

    def _handle_install(self) -> None:
        spec = self._install_entry.get().strip()
        if spec:
            self._on_install(spec)
            self._install_entry.delete(0, "end")

    def _handle_install_enter(self, _event=None) -> None:
        self._handle_install()

    def _handle_export(self, choice: str) -> None:
        mapping = {
            "Export CSV": "csv",
            "Export Excel": "excel",
            "Export PDF": "pdf",
        }
        fmt = mapping.get(choice)
        if fmt:
            self._on_export(fmt)
        self._export_menu.set("Export ▾")

    def set_busy(self, busy: bool) -> None:
        state = "disabled" if busy else "normal"
        for widget in (
            self._refresh_btn,
            self._install_btn,
            self._sort_menu,
            self._export_menu,
        ):
            widget.configure(state=state)
