"""
core/package_scanner.py

Scans an arbitrary Python interpreter for its installed packages. Since
we can't `import importlib.metadata` for an interpreter that isn't the
one currently running, we shell out to that interpreter and ask it to
report its own packages as JSON. This correctly handles the case where
the user has 5 different Python installs, each with different packages.
"""

from __future__ import annotations

import json
import platform
import subprocess
from pathlib import Path

from core.models import PackageInfo, PythonInterpreter
from utils.logger import get_logger

logger = get_logger(__name__)

IS_WINDOWS = platform.system() == "Windows"

# This little program is executed *inside* the target interpreter so
# that package discovery always matches that interpreter's environment.
_SCANNER_SCRIPT = r"""
import json
import sys
from importlib import metadata

packages = []
for dist in metadata.distributions():
    try:
        name = dist.metadata["Name"] or dist.metadata.get("Summary", "unknown")
        version = dist.version or "0.0.0"
        location = str(dist.locate_file("")) if dist.locate_file else ""
        summary = dist.metadata.get("Summary", "") or ""
        author = dist.metadata.get("Author", "") or dist.metadata.get("Author-email", "") or ""
        homepage = dist.metadata.get("Home-page", "") or dist.metadata.get("Project-URL", "") or ""
        requires = list(dist.requires or [])
        editable = False
        try:
            direct_url = dist.read_text("direct_url.json")
            if direct_url and '"editable": true' in direct_url:
                editable = True
        except Exception:
            pass

        size = 0
        try:
            base = dist.locate_file("")
            record = dist.read_text("RECORD")
            if record and base:
                import os
                seen = set()
                for line in record.splitlines():
                    rel = line.split(",")[0]
                    full = os.path.join(str(base), rel)
                    if full not in seen and os.path.isfile(full):
                        seen.add(full)
                        try:
                            size += os.path.getsize(full)
                        except OSError:
                            pass
        except Exception:
            pass

        packages.append({
            "name": name,
            "version": version,
            "location": location,
            "size_bytes": size,
            "summary": summary,
            "author": author,
            "homepage": homepage,
            "requires": requires,
            "is_editable": editable,
        })
    except Exception:
        continue

print(json.dumps(packages))
"""


class PackageScanError(RuntimeError):
    """Raised when a target interpreter can't be scanned."""


class PackageScanner:
    """Lists installed packages for a given PythonInterpreter."""

    def scan(self, interpreter: PythonInterpreter, timeout: float = 30.0) -> list[PackageInfo]:
        """Return every package installed for `interpreter`."""
        logger.info("Scanning packages for %s", interpreter.display_name)
        try:
            completed = subprocess.run(
                [str(interpreter.executable), "-c", _SCANNER_SCRIPT],
                capture_output=True,
                text=True,
                timeout=timeout,
                creationflags=subprocess.CREATE_NO_WINDOW if IS_WINDOWS else 0,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            raise PackageScanError(f"Failed to run interpreter: {exc}") from exc

        if completed.returncode != 0:
            raise PackageScanError(
                f"Interpreter exited with code {completed.returncode}: {completed.stderr.strip()}"
            )

        stdout = completed.stdout.strip()
        if not stdout:
            return []

        try:
            raw_packages = json.loads(stdout.splitlines()[-1])
        except (json.JSONDecodeError, IndexError) as exc:
            raise PackageScanError(f"Could not parse scanner output: {exc}") from exc

        packages: list[PackageInfo] = []
        for raw in raw_packages:
            packages.append(
                PackageInfo(
                    name=raw.get("name", "unknown"),
                    version=raw.get("version", "0.0.0"),
                    location=Path(raw["location"]) if raw.get("location") else None,
                    size_bytes=int(raw.get("size_bytes", 0)),
                    summary=raw.get("summary", ""),
                    author=raw.get("author", ""),
                    homepage=raw.get("homepage", ""),
                    requires=raw.get("requires", []) or [],
                    is_editable=bool(raw.get("is_editable", False)),
                )
            )

        packages.sort(key=lambda p: p.name.lower())
        logger.info("Found %d package(s) for %s", len(packages), interpreter.display_name)
        return packages

    def check_outdated(
        self, interpreter: PythonInterpreter, timeout: float = 60.0
    ) -> dict[str, str]:
        """Return {package_name: latest_version} for outdated packages via pip."""
        try:
            completed = subprocess.run(
                [
                    str(interpreter.executable),
                    "-m",
                    "pip",
                    "list",
                    "--outdated",
                    "--format=json",
                ],
                capture_output=True,
                text=True,
                timeout=timeout,
                creationflags=subprocess.CREATE_NO_WINDOW if IS_WINDOWS else 0,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            logger.warning("Failed to check outdated packages: %s", exc)
            return {}

        if completed.returncode != 0 or not completed.stdout.strip():
            return {}

        try:
            data = json.loads(completed.stdout.strip())
        except json.JSONDecodeError:
            return {}

        return {entry["name"]: entry["latest_version"] for entry in data}
