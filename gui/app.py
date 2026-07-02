"""
gui/app.py

The main application window. Wires together the sidebar, toolbar, and
package table, and coordinates background work (interpreter detection,
package scanning, install/uninstall/upgrade, export) through
BackgroundTaskRunner so the UI thread is never blocked.
"""

from __future__ import annotations

import platform
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk

from core.exporter import ExportDependencyError, Exporter
from core.models import OperationResult, PackageInfo, PythonInterpreter
from core.package_manager import PackageManager
from core.package_scanner import PackageScanError, PackageScanner
from core.python_detector import PythonDetector
from gui import theme
from gui.package_table import PackageTable
from gui.sidebar import Sidebar
from gui.toolbar import Toolbar
from utils.logger import get_logger
from utils.threading_utils import BackgroundTaskRunner

logger = get_logger(__name__)

APP_TITLE = "PyPackage Manager Pro"
APP_MIN_SIZE = (1100, 650)


class App(ctk.CTk):
    """Root application window."""

    def __init__(self) -> None:
        super().__init__()

        ctk.set_appearance_mode("dark")
        try:
            ctk.set_default_color_theme(str(theme.write_theme_file()))
        except Exception:
            logger.warning("Falling back to built-in 'dark-blue' theme", exc_info=True)
            ctk.set_default_color_theme("dark-blue")

        self.title(APP_TITLE)
        self.geometry("1300x780")
        self.minsize(*APP_MIN_SIZE)
        self.configure(fg_color=theme.BG_PRIMARY)

        self._detector = PythonDetector()
        self._scanner = PackageScanner()
        self._manager = PackageManager()
        self._exporter = Exporter()
        self._tasks = BackgroundTaskRunner(max_workers=4)

        self._interpreters: list[PythonInterpreter] = []
        self._current_interpreter: PythonInterpreter | None = None
        self._search_term: str = ""
        self._sort_mode: str = "Name (A-Z)"

        self._build_layout()
        self._refresh_interpreters()

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------
    def _build_layout(self) -> None:
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.sidebar = Sidebar(
            self,
            on_select=self._handle_interpreter_selected,
            on_refresh=self._refresh_interpreters,
            width=260,
        )
        self.sidebar.grid(row=0, column=0, sticky="nsw")
        self.sidebar.grid_propagate(False)

        right_panel = ctk.CTkFrame(self, fg_color=theme.BG_PRIMARY, corner_radius=0)
        right_panel.grid(row=0, column=1, sticky="nsew")
        right_panel.grid_rowconfigure(1, weight=1)
        right_panel.grid_columnconfigure(0, weight=1)

        self.toolbar = Toolbar(
            right_panel,
            on_search=self._handle_search,
            on_sort_change=self._handle_sort_change,
            on_refresh=self._refresh_packages,
            on_export=self._handle_export,
            on_install=self._handle_install,
        )
        self.toolbar.grid(row=0, column=0, sticky="ew")

        self.table = PackageTable(
            right_panel,
            on_uninstall=self._handle_uninstall,
            on_upgrade=self._handle_upgrade,
        )
        self.table.grid(row=1, column=0, sticky="nsew")

        self.status_bar = ctk.CTkLabel(
            right_panel,
            text=self._platform_summary(),
            font=("Segoe UI", 10),
            text_color=theme.TEXT_MUTED,
            anchor="w",
        )
        self.status_bar.grid(row=2, column=0, sticky="ew", padx=16, pady=4)

    @staticmethod
    def _platform_summary() -> str:
        return f"{platform.system()} {platform.release()} · PyPackage Manager Pro"

    def _set_status(self, text: str) -> None:
        self.status_bar.configure(text=text)

    # ------------------------------------------------------------------
    # Interpreter detection
    # ------------------------------------------------------------------
    def _refresh_interpreters(self) -> None:
        self.sidebar.set_loading(True)
        self._set_status("Detecting Python interpreters...")
        self._tasks.run(
            self,
            self._detector.detect_all,
            on_success=self._on_interpreters_detected,
            on_error=self._on_interpreters_error,
        )

    def _on_interpreters_detected(self, interpreters: list[PythonInterpreter]) -> None:
        self._interpreters = interpreters
        self.sidebar.set_loading(False)
        self.sidebar.populate(interpreters)
        if not interpreters:
            self._set_status("No Python interpreters found.")
            self.table.render([])

    def _on_interpreters_error(self, exc: BaseException) -> None:
        self.sidebar.set_loading(False)
        self._set_status(f"Interpreter detection failed: {exc}")
        messagebox.showerror(APP_TITLE, f"Failed to detect Python interpreters:\n{exc}")

    def _handle_interpreter_selected(self, interpreter: PythonInterpreter) -> None:
        self._current_interpreter = interpreter
        self._refresh_packages()

    # ------------------------------------------------------------------
    # Package scanning
    # ------------------------------------------------------------------
    def _refresh_packages(self) -> None:
        if self._current_interpreter is None:
            return
        self.toolbar.set_busy(True)
        self._set_status(f"Scanning packages for {self._current_interpreter.display_name}...")
        self._tasks.run(
            self,
            self._scan_and_check_outdated,
            on_success=self._on_packages_scanned,
            on_error=self._on_packages_error,
        )

    def _scan_and_check_outdated(self) -> list[PackageInfo]:
        assert self._current_interpreter is not None
        packages = self._scanner.scan(self._current_interpreter)
        outdated = self._scanner.check_outdated(self._current_interpreter)
        for pkg in packages:
            if pkg.name in outdated:
                pkg.latest_version = outdated[pkg.name]
        return packages

    def _on_packages_scanned(self, packages: list[PackageInfo]) -> None:
        self.toolbar.set_busy(False)
        self.table.set_packages(packages)
        self._apply_filters_and_sort()
        interp = self._current_interpreter
        if interp is not None:
            self._set_status(f"Ready · {interp.display_name}")

    def _on_packages_error(self, exc: BaseException) -> None:
        self.toolbar.set_busy(False)
        message = str(exc)
        if isinstance(exc, PackageScanError):
            message = f"Could not scan packages: {exc}"
        self._set_status(message)
        messagebox.showerror(APP_TITLE, message)

    # ------------------------------------------------------------------
    # Search / sort / filter
    # ------------------------------------------------------------------
    def _handle_search(self, term: str) -> None:
        self._search_term = term.strip().lower()
        self._apply_filters_and_sort()

    def _handle_sort_change(self, mode: str) -> None:
        self._sort_mode = mode
        self._apply_filters_and_sort()

    def _apply_filters_and_sort(self) -> None:
        packages = list(self.table.get_all())

        if self._search_term:
            packages = [
                p
                for p in packages
                if self._search_term in p.name.lower() or self._search_term in p.summary.lower()
            ]

        sort_key = {
            "Name (A-Z)": lambda p: p.name.lower(),
            "Name (Z-A)": lambda p: p.name.lower(),
            "Version": lambda p: p.version,
            "Size (Largest)": lambda p: p.size_bytes,
            "Size (Smallest)": lambda p: p.size_bytes,
        }.get(self._sort_mode, lambda p: p.name.lower())

        reverse = self._sort_mode in ("Name (Z-A)", "Size (Largest)")
        packages.sort(key=sort_key, reverse=reverse)

        self.table.render(packages)

    # ------------------------------------------------------------------
    # Install / uninstall / upgrade
    # ------------------------------------------------------------------
    def _handle_install(self, spec: str) -> None:
        if self._current_interpreter is None:
            messagebox.showwarning(APP_TITLE, "Select a Python interpreter first.")
            return
        self.toolbar.set_busy(True)
        self._set_status(f"Installing {spec}...")
        self._tasks.run(
            self,
            self._manager.install,
            on_success=self._on_operation_done,
            on_error=self._on_packages_error,
            interpreter=self._current_interpreter,
            spec=spec,
        )

    def _handle_upgrade(self, package: PackageInfo) -> None:
        if self._current_interpreter is None:
            return
        self.toolbar.set_busy(True)
        self._set_status(f"Upgrading {package.name}...")
        self._tasks.run(
            self,
            self._manager.upgrade,
            on_success=self._on_operation_done,
            on_error=self._on_packages_error,
            interpreter=self._current_interpreter,
            package_name=package.name,
        )

    def _handle_uninstall(self, package: PackageInfo) -> None:
        if self._current_interpreter is None:
            return
        confirmed = messagebox.askyesno(
            APP_TITLE, f"Uninstall '{package.name}' ({package.version})?"
        )
        if not confirmed:
            return
        self.toolbar.set_busy(True)
        self._set_status(f"Uninstalling {package.name}...")
        self._tasks.run(
            self,
            self._manager.uninstall,
            on_success=self._on_operation_done,
            on_error=self._on_packages_error,
            interpreter=self._current_interpreter,
            package_name=package.name,
        )

    def _on_operation_done(self, result: OperationResult) -> None:
        self.toolbar.set_busy(False)
        if result.success:
            self._set_status(result.message.splitlines()[-1] if result.message else "Done.")
        else:
            self._set_status(f"Operation failed: {result.message}")
            messagebox.showerror(APP_TITLE, f"{result.package_name}: {result.message}")
        self._refresh_packages()

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------
    def _handle_export(self, fmt: str) -> None:
        if self._current_interpreter is None:
            messagebox.showwarning(APP_TITLE, "Select a Python interpreter first.")
            return
        packages = self.table.get_all()
        if not packages:
            messagebox.showinfo(APP_TITLE, "No packages to export.")
            return

        extensions = {"csv": ".csv", "excel": ".xlsx", "pdf": ".pdf"}
        ext = extensions[fmt]
        default_name = f"packages_{self._current_interpreter.version}{ext}"
        out_path = filedialog.asksaveasfilename(
            title="Export packages",
            defaultextension=ext,
            initialfile=default_name,
            initialdir=str(Path(__file__).resolve().parent.parent / "exports"),
            filetypes=[(fmt.upper(), f"*{ext}")],
        )
        if not out_path:
            return

        self._set_status(f"Exporting to {fmt.upper()}...")
        self._tasks.run(
            self,
            self._run_export,
            on_success=self._on_export_done,
            on_error=self._on_export_error,
            fmt=fmt,
            packages=packages,
            out_path=Path(out_path),
        )

    def _run_export(self, fmt: str, packages: list[PackageInfo], out_path: Path) -> Path:
        assert self._current_interpreter is not None
        method = {
            "csv": self._exporter.export_csv,
            "excel": self._exporter.export_excel,
            "pdf": self._exporter.export_pdf,
        }[fmt]
        return method(packages, self._current_interpreter, out_path)

    def _on_export_done(self, out_path: Path) -> None:
        self._set_status(f"Exported to {out_path}")
        messagebox.showinfo(APP_TITLE, f"Export complete:\n{out_path}")

    def _on_export_error(self, exc: BaseException) -> None:
        message = str(exc)
        if isinstance(exc, ExportDependencyError):
            message = str(exc)
        self._set_status(f"Export failed: {message}")
        messagebox.showerror(APP_TITLE, message)

    def on_close(self) -> None:
        self._tasks.shutdown(wait=False)
        self.destroy()
