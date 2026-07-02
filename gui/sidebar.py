"""
gui/sidebar.py

Left-hand sidebar: lists every detected Python interpreter as a
selectable card, plus a "Refresh" button to re-run detection.
"""

from __future__ import annotations

from typing import Callable

import customtkinter as ctk

from core.models import PythonInterpreter
from gui import theme


class InterpreterCard(ctk.CTkFrame):
    """A single clickable card representing one Python interpreter."""

    def __init__(
        self,
        master: ctk.CTkBaseClass,
        interpreter: PythonInterpreter,
        on_select: Callable[[PythonInterpreter], None],
        **kwargs,
    ) -> None:
        super().__init__(master, corner_radius=10, fg_color=theme.BG_CARD, **kwargs)
        self.interpreter = interpreter
        self._on_select = on_select
        self._selected = False

        self.grid_columnconfigure(0, weight=1)

        self._dot = ctk.CTkLabel(
            self, text="●", text_color=theme.ACCENT, font=("Segoe UI", 14), width=16
        )
        self._dot.grid(row=0, column=0, rowspan=2, sticky="w", padx=(10, 0), pady=8)

        self._version_label = ctk.CTkLabel(
            self,
            text=f"Python {interpreter.version}",
            font=("Segoe UI", 13, "bold"),
            text_color=theme.TEXT_PRIMARY,
            anchor="w",
        )
        self._version_label.grid(row=0, column=1, sticky="w", padx=(4, 10), pady=(8, 0))

        self._source_label = ctk.CTkLabel(
            self,
            text=f"{interpreter.architecture} · {interpreter.source.value}",
            font=("Segoe UI", 10),
            text_color=theme.TEXT_SECONDARY,
            anchor="w",
        )
        self._source_label.grid(row=1, column=1, sticky="w", padx=(4, 10), pady=(0, 8))

        for widget in (self, self._dot, self._version_label, self._source_label):
            widget.bind("<Button-1>", self._handle_click)
            widget.bind("<Enter>", self._handle_enter)
            widget.bind("<Leave>", self._handle_leave)

    def _handle_click(self, _event=None) -> None:
        self._on_select(self.interpreter)

    def _handle_enter(self, _event=None) -> None:
        if not self._selected:
            self.configure(fg_color=theme.BG_HOVER)

    def _handle_leave(self, _event=None) -> None:
        if not self._selected:
            self.configure(fg_color=theme.BG_CARD)

    def set_selected(self, selected: bool) -> None:
        self._selected = selected
        self.configure(fg_color=theme.ACCENT_DARK if selected else theme.BG_CARD)


class Sidebar(ctk.CTkFrame):
    """Scrollable list of interpreter cards with a refresh button."""

    def __init__(
        self,
        master: ctk.CTkBaseClass,
        on_select: Callable[[PythonInterpreter], None],
        on_refresh: Callable[[], None],
        **kwargs,
    ) -> None:
        super().__init__(master, corner_radius=0, fg_color=theme.BG_SIDEBAR, **kwargs)
        self._on_select = on_select
        self._on_refresh = on_refresh
        self._cards: list[InterpreterCard] = []

        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        header = ctk.CTkLabel(
            self,
            text="🐍  Interpreters",
            font=("Segoe UI", 15, "bold"),
            text_color=theme.TEXT_PRIMARY,
            anchor="w",
        )
        header.grid(row=0, column=0, sticky="ew", padx=16, pady=(16, 8))

        self._refresh_btn = ctk.CTkButton(
            self,
            text="⟳ Refresh",
            command=self._handle_refresh,
            height=32,
            fg_color=theme.ACCENT_DARK,
            hover_color=theme.ACCENT_HOVER,
        )
        self._refresh_btn.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 12))

        self._scroll_frame = ctk.CTkScrollableFrame(
            self, fg_color="transparent", scrollbar_button_color=theme.BORDER
        )
        self._scroll_frame.grid(row=2, column=0, sticky="nsew", padx=8, pady=(0, 8))
        self._scroll_frame.grid_columnconfigure(0, weight=1)

        self._status_label = ctk.CTkLabel(
            self,
            text="",
            font=("Segoe UI", 10),
            text_color=theme.TEXT_MUTED,
            wraplength=200,
            justify="left",
        )
        self._status_label.grid(row=3, column=0, sticky="ew", padx=16, pady=(0, 12))

    def _handle_refresh(self) -> None:
        self._on_refresh()

    def set_loading(self, loading: bool) -> None:
        self._refresh_btn.configure(
            state="disabled" if loading else "normal",
            text="⟳ Scanning..." if loading else "⟳ Refresh",
        )
        self._status_label.configure(
            text="Scanning for interpreters..." if loading else self._status_label.cget("text")
        )

    def populate(self, interpreters: list[PythonInterpreter]) -> None:
        """Rebuild the interpreter card list."""
        for card in self._cards:
            card.destroy()
        self._cards.clear()

        for idx, interp in enumerate(interpreters):
            card = InterpreterCard(
                self._scroll_frame, interp, on_select=self._handle_select
            )
            card.grid(row=idx, column=0, sticky="ew", pady=4, padx=4)
            self._cards.append(card)

        count = len(interpreters)
        self._status_label.configure(
            text=f"{count} interpreter{'s' if count != 1 else ''} found"
        )

        if interpreters:
            self._handle_select(interpreters[0])

    def _handle_select(self, interpreter: PythonInterpreter) -> None:
        for card in self._cards:
            card.set_selected(card.interpreter.key == interpreter.key)
        self._on_select(interpreter)
