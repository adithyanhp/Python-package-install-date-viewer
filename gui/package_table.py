"""
gui/package_table.py

Main content area: a scrollable "table" of installed packages built
from CTkFrame rows (CustomTkinter has no native table widget). Each
row shows name/version/size/summary plus Upgrade / Uninstall buttons.
"""

from __future__ import annotations

from typing import Callable

import customtkinter as ctk

from core.models import PackageInfo
from gui import theme

_HEADERS = ("Package", "Version", "Latest", "Size", "Summary", "Actions")
_COL_WEIGHTS = (2, 1, 1, 1, 3, 2)


class PackageRow(ctk.CTkFrame):
    """A single package row with name, version, size, and action buttons."""

    def __init__(
        self,
        master: ctk.CTkBaseClass,
        package: PackageInfo,
        on_uninstall: Callable[[PackageInfo], None],
        on_upgrade: Callable[[PackageInfo], None],
        striped: bool = False,
        **kwargs,
    ) -> None:
        bg = theme.BG_CARD if striped else theme.BG_SECONDARY
        super().__init__(master, corner_radius=6, fg_color=bg, **kwargs)
        self.package = package

        for col, weight in enumerate(_COL_WEIGHTS):
            self.grid_columnconfigure(col, weight=weight)

        name_text = package.name + (" (editable)" if package.is_editable else "")
        ctk.CTkLabel(
            self, text=name_text, anchor="w", font=("Segoe UI", 12, "bold"),
            text_color=theme.TEXT_PRIMARY,
        ).grid(row=0, column=0, sticky="ew", padx=(12, 4), pady=8)

        ctk.CTkLabel(
            self, text=package.version, anchor="w", text_color=theme.TEXT_SECONDARY
        ).grid(row=0, column=1, sticky="ew", padx=4, pady=8)

        latest_text = package.latest_version or "—"
        latest_color = theme.WARNING if package.has_update else theme.TEXT_MUTED
        ctk.CTkLabel(
            self, text=latest_text, anchor="w", text_color=latest_color
        ).grid(row=0, column=2, sticky="ew", padx=4, pady=8)

        ctk.CTkLabel(
            self, text=package.size_human, anchor="w", text_color=theme.TEXT_SECONDARY
        ).grid(row=0, column=3, sticky="ew", padx=4, pady=8)

        summary = package.summary[:70] + "…" if len(package.summary) > 70 else package.summary
        ctk.CTkLabel(
            self, text=summary or "—", anchor="w", text_color=theme.TEXT_MUTED,
            font=("Segoe UI", 11),
        ).grid(row=0, column=4, sticky="ew", padx=4, pady=8)

        actions = ctk.CTkFrame(self, fg_color="transparent")
        actions.grid(row=0, column=5, sticky="e", padx=(4, 12), pady=6)

        upgrade_btn = ctk.CTkButton(
            actions,
            text="⬆ Upgrade",
            width=80,
            height=26,
            font=("Segoe UI", 11),
            fg_color=theme.ACCENT_DARK,
            hover_color=theme.ACCENT_HOVER,
            command=lambda: on_upgrade(package),
            state="normal" if package.has_update else "disabled",
        )
        upgrade_btn.pack(side="left", padx=(0, 6))

        uninstall_btn = ctk.CTkButton(
            actions,
            text="🗑 Remove",
            width=80,
            height=26,
            font=("Segoe UI", 11),
            fg_color=theme.DANGER,
            hover_color="#D95555",
            text_color="#2A0E0E",
            command=lambda: on_uninstall(package),
        )
        uninstall_btn.pack(side="left")


class PackageTable(ctk.CTkFrame):
    """Scrollable list of PackageRow widgets, with header and empty state."""

    def __init__(
        self,
        master: ctk.CTkBaseClass,
        on_uninstall: Callable[[PackageInfo], None],
        on_upgrade: Callable[[PackageInfo], None],
        **kwargs,
    ) -> None:
        super().__init__(master, corner_radius=0, fg_color=theme.BG_PRIMARY, **kwargs)
        self._on_uninstall = on_uninstall
        self._on_upgrade = on_upgrade
        self._rows: list[PackageRow] = []
        self._all_packages: list[PackageInfo] = []

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        header = ctk.CTkFrame(self, fg_color=theme.BG_SIDEBAR, corner_radius=0, height=36)
        header.grid(row=0, column=0, sticky="ew")
        for col, (weight, text) in enumerate(zip(_COL_WEIGHTS, _HEADERS)):
            header.grid_columnconfigure(col, weight=weight)
            ctk.CTkLabel(
                header, text=text, font=("Segoe UI", 11, "bold"),
                text_color=theme.TEXT_SECONDARY, anchor="w",
            ).grid(row=0, column=col, sticky="ew", padx=12, pady=6)

        self._scroll_frame = ctk.CTkScrollableFrame(
            self, fg_color="transparent", scrollbar_button_color=theme.BORDER
        )
        self._scroll_frame.grid(row=1, column=0, sticky="nsew", padx=8, pady=8)
        self._scroll_frame.grid_columnconfigure(0, weight=1)

        self._empty_label = ctk.CTkLabel(
            self._scroll_frame,
            text="No packages to display.\nSelect an interpreter or adjust your search.",
            text_color=theme.TEXT_MUTED,
            font=("Segoe UI", 13),
            justify="center",
        )

        self._summary_label = ctk.CTkLabel(
            self, text="", font=("Segoe UI", 11), text_color=theme.TEXT_MUTED, anchor="w"
        )
        self._summary_label.grid(row=2, column=0, sticky="ew", padx=16, pady=(0, 8))

    def set_packages(self, packages: list[PackageInfo]) -> None:
        """Replace the full package list (called after a scan/refresh)."""
        self._all_packages = packages
        self.render(packages)

    def render(self, packages: list[PackageInfo]) -> None:
        """Render a (possibly filtered/sorted) subset of packages."""
        for row in self._rows:
            row.destroy()
        self._rows.clear()
        self._empty_label.grid_forget()

        if not packages:
            self._empty_label.grid(row=0, column=0, pady=40)
            self._summary_label.configure(text="0 packages")
            return

        total_size = sum(p.size_bytes for p in packages)
        total_str = self._human_size(total_size)
        outdated = sum(1 for p in packages if p.has_update)
        self._summary_label.configure(
            text=f"{len(packages)} package(s) · {total_str} total"
            + (f" · {outdated} update(s) available" if outdated else "")
        )

        for idx, pkg in enumerate(packages):
            row = PackageRow(
                self._scroll_frame,
                pkg,
                on_uninstall=self._on_uninstall,
                on_upgrade=self._on_upgrade,
                striped=(idx % 2 == 0),
            )
            row.grid(row=idx, column=0, sticky="ew", pady=2, padx=2)
            self._rows.append(row)

    @staticmethod
    def _human_size(size_bytes: int) -> str:
        size = float(size_bytes)
        for unit in ("B", "KB", "MB", "GB"):
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"

    def get_all(self) -> list[PackageInfo]:
        return self._all_packages
