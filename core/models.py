"""
core/models.py

Dataclasses shared across the application. Keeping these in one module
avoids circular imports between core/ and gui/.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from enum import Enum


class InterpreterSource(str, Enum):
    """Where a Python interpreter was discovered."""

    REGISTRY = "Windows Registry"
    PY_LAUNCHER = "py Launcher"
    PATH = "PATH"
    VENV = "Virtual Environment"
    CONDA = "Conda"
    UNKNOWN = "Unknown"


@dataclass(frozen=True, slots=True)
class PythonInterpreter:
    """Represents a single discovered Python interpreter."""

    executable: Path
    version: str
    architecture: str
    source: InterpreterSource
    display_name: str = ""

    def __post_init__(self) -> None:
        if not self.display_name:
            object.__setattr__(
                self,
                "display_name",
                f"Python {self.version} ({self.architecture}) - {self.source.value}",
            )

    @property
    def key(self) -> str:
        """Unique identifier used for dict lookups / caching."""
        return str(self.executable).lower()


@dataclass(slots=True)
class PackageInfo:
    """Represents a single installed package for a given interpreter."""

    name: str
    version: str
    location: Path | None = None
    size_bytes: int = 0
    summary: str = ""
    author: str = ""
    homepage: str = ""
    requires: list[str] = field(default_factory=list)
    installed_at: datetime | None = None
    is_editable: bool = False
    latest_version: str | None = None

    @property
    def size_human(self) -> str:
        """Human readable size, e.g. '1.2 MB'."""
        size = float(self.size_bytes)
        for unit in ("B", "KB", "MB", "GB"):
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"

    @property
    def has_update(self) -> bool:
        return bool(self.latest_version) and self.latest_version != self.version


@dataclass(slots=True)
class OperationResult:
    """Result of a pip operation (install/uninstall/upgrade)."""

    success: bool
    message: str
    package_name: str = ""
    returncode: int | None = None
