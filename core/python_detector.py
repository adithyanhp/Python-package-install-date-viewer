"""
core/python_detector.py

Detects every Python interpreter available on the machine using several
independent strategies:

  1. Windows Registry            (HKCU/HKLM ... Python\\PythonCore)
  2. `py` launcher                (`py -0p`)
  3. PATH environment variable    (every `python*.exe` on PATH)
  4. Virtual environments         (common venv locations + PATH parents)
  5. Conda / Miniconda            (`conda env list` + default install dirs)

Results are de-duplicated by resolved executable path. This module is
platform-aware: registry / py-launcher detection only runs on Windows,
but PATH / venv / conda detection degrade gracefully on other
platforms so the rest of the app can still be exercised in tests.
"""

from __future__ import annotations

import os
import platform
import re
import shutil
import subprocess
from pathlib import Path

from core.models import InterpreterSource, PythonInterpreter
from utils.logger import get_logger

logger = get_logger(__name__)

IS_WINDOWS = platform.system() == "Windows"

_VERSION_RE = re.compile(r"(\d+\.\d+\.\d+)")


def _run(cmd: list[str], timeout: float = 5.0) -> str:
    """Run a command and return stdout, or '' on any failure."""
    try:
        completed = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            creationflags=subprocess.CREATE_NO_WINDOW if IS_WINDOWS else 0,
        )
        return completed.stdout.strip()
    except (OSError, subprocess.SubprocessError) as exc:
        logger.debug("Command failed %s: %s", cmd, exc)
        return ""


def _probe_interpreter(executable: Path) -> tuple[str, str] | None:
    """Return (version, architecture) for an interpreter, or None."""
    if not executable.exists():
        return None
    output = _run(
        [
            str(executable),
            "-c",
            "import sys,platform;"
            "print(platform.python_version());"
            "print(64 if sys.maxsize > 2**32 else 32)",
        ]
    )
    lines = [line.strip() for line in output.splitlines() if line.strip()]
    if len(lines) < 2:
        return None
    version, bits = lines[0], lines[1]
    if not _VERSION_RE.match(version):
        return None
    arch = "64-bit" if bits == "64" else "32-bit"
    return version, arch


class PythonDetector:
    """Aggregates all detection strategies and returns unique interpreters."""

    def __init__(self) -> None:
        self._found: dict[str, PythonInterpreter] = {}

    def detect_all(self) -> list[PythonInterpreter]:
        """Run every detection strategy and return sorted, unique results."""
        self._found.clear()

        strategies = (
            self._detect_registry,
            self._detect_py_launcher,
            self._detect_path,
            self._detect_venvs,
            self._detect_conda,
        )

        for strategy in strategies:
            try:
                for interp in strategy():
                    self._add(interp)
            except Exception as exc:  # noqa: BLE001 - never let one strategy kill the rest
                logger.exception("Detection strategy %s failed: %s", strategy.__name__, exc)

        results = sorted(
            self._found.values(),
            key=lambda i: (i.version, i.display_name),
            reverse=True,
        )
        logger.info("Detected %d unique Python interpreter(s)", len(results))
        return results

    def _add(self, interp: PythonInterpreter | None) -> None:
        if interp is None:
            return
        try:
            resolved = str(interp.executable.resolve()).lower()
        except OSError:
            resolved = interp.key
        if resolved not in self._found:
            self._found[resolved] = interp

    # ------------------------------------------------------------------
    # Strategy: Windows Registry
    # ------------------------------------------------------------------
    def _detect_registry(self) -> list[PythonInterpreter]:
        if not IS_WINDOWS:
            return []
        try:
            import winreg
        except ImportError:
            return []

        results: list[PythonInterpreter] = []
        hives = (
            (winreg.HKEY_CURRENT_USER, InterpreterSource.REGISTRY),
            (winreg.HKEY_LOCAL_MACHINE, InterpreterSource.REGISTRY),
        )
        base_paths = (r"SOFTWARE\Python\PythonCore", r"SOFTWARE\WOW6432Node\Python\PythonCore")

        for hive, source in hives:
            for base_path in base_paths:
                try:
                    with winreg.OpenKey(hive, base_path) as base_key:
                        i = 0
                        while True:
                            try:
                                version_tag = winreg.EnumKey(base_key, i)
                            except OSError:
                                break
                            i += 1
                            try:
                                install_key = winreg.OpenKey(
                                    base_key, f"{version_tag}\\InstallPath"
                                )
                                exe_path, _ = winreg.QueryValueEx(install_key, "ExecutablePath")
                            except OSError:
                                continue
                            executable = Path(exe_path)
                            probe = _probe_interpreter(executable)
                            if probe is None:
                                continue
                            version, arch = probe
                            results.append(
                                PythonInterpreter(
                                    executable=executable,
                                    version=version,
                                    architecture=arch,
                                    source=source,
                                )
                            )
                except OSError:
                    continue
        return results

    # ------------------------------------------------------------------
    # Strategy: `py` launcher
    # ------------------------------------------------------------------
    def _detect_py_launcher(self) -> list[PythonInterpreter]:
        py_exe = shutil.which("py")
        if py_exe is None:
            return []
        output = _run([py_exe, "-0p"])
        results: list[PythonInterpreter] = []
        for line in output.splitlines():
            line = line.strip()
            match = re.search(r"(-V:)?[\d.\-]*\s*(.+?\.exe)", line)
            if not match:
                continue
            exe_path = Path(match.group(2).strip().strip("*").strip())
            probe = _probe_interpreter(exe_path)
            if probe is None:
                continue
            version, arch = probe
            results.append(
                PythonInterpreter(
                    executable=exe_path,
                    version=version,
                    architecture=arch,
                    source=InterpreterSource.PY_LAUNCHER,
                )
            )
        return results

    # ------------------------------------------------------------------
    # Strategy: PATH
    # ------------------------------------------------------------------
    def _detect_path(self) -> list[PythonInterpreter]:
        names = ("python.exe", "python3.exe") if IS_WINDOWS else ("python3", "python")
        found_paths: set[Path] = set()
        for directory in os.environ.get("PATH", "").split(os.pathsep):
            if not directory:
                continue
            dir_path = Path(directory)
            for name in names:
                candidate = dir_path / name
                if candidate.exists():
                    found_paths.add(candidate)

        results: list[PythonInterpreter] = []
        for exe in found_paths:
            probe = _probe_interpreter(exe)
            if probe is None:
                continue
            version, arch = probe
            results.append(
                PythonInterpreter(
                    executable=exe,
                    version=version,
                    architecture=arch,
                    source=InterpreterSource.PATH,
                )
            )
        return results

    # ------------------------------------------------------------------
    # Strategy: Virtual environments
    # ------------------------------------------------------------------
    def _detect_venvs(self) -> list[PythonInterpreter]:
        search_roots = [
            Path.home(),
            Path.home() / "Projects",
            Path.home() / "source" / "repos",
            Path.cwd(),
        ]
        exe_name = "python.exe" if IS_WINDOWS else "python3"
        scripts_dir = "Scripts" if IS_WINDOWS else "bin"

        results: list[PythonInterpreter] = []
        seen_dirs: set[Path] = set()

        for root in search_roots:
            if not root.exists():
                continue
            try:
                children = list(root.iterdir())
            except OSError:
                continue
            for child in children:
                if not child.is_dir():
                    continue
                cfg = child / "pyvenv.cfg"
                if not cfg.exists():
                    continue
                exe = child / scripts_dir / exe_name
                if exe in seen_dirs:
                    continue
                seen_dirs.add(exe)
                probe = _probe_interpreter(exe)
                if probe is None:
                    continue
                version, arch = probe
                results.append(
                    PythonInterpreter(
                        executable=exe,
                        version=version,
                        architecture=arch,
                        source=InterpreterSource.VENV,
                        display_name=f"venv: {child.name} (Python {version})",
                    )
                )
        return results

    # ------------------------------------------------------------------
    # Strategy: Conda / Miniconda
    # ------------------------------------------------------------------
    def _detect_conda(self) -> list[PythonInterpreter]:
        conda_exe = shutil.which("conda")
        if conda_exe is None:
            return []
        output = _run([conda_exe, "env", "list"])
        results: list[PythonInterpreter] = []
        for line in output.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if not parts:
                continue
            env_name = parts[0]
            env_path = Path(parts[-1])
            exe = env_path / ("python.exe" if IS_WINDOWS else "bin/python")
            probe = _probe_interpreter(exe)
            if probe is None:
                continue
            version, arch = probe
            results.append(
                PythonInterpreter(
                    executable=exe,
                    version=version,
                    architecture=arch,
                    source=InterpreterSource.CONDA,
                    display_name=f"conda: {env_name} (Python {version})",
                )
            )
        return results
