"""
core/package_manager.py

Wraps pip operations (install, uninstall, upgrade) for a given target
interpreter. All subprocess calls are executed safely - arguments are
passed as a list (never through a shell), and package names are
validated before being handed to pip.
"""

from __future__ import annotations

import platform
import re
import subprocess

from core.models import OperationResult, PythonInterpreter
from utils.logger import get_logger

logger = get_logger(__name__)

IS_WINDOWS = platform.system() == "Windows"

# Conservative allow-list for package specifiers, e.g. "requests==2.31.0",
# "numpy>=1.20,<2.0", "some-package[extra]". Rejects shell metacharacters.
_SAFE_SPEC_RE = re.compile(r"^[A-Za-z0-9._\-\[\]<>=!,~ ]+$")


class UnsafePackageSpecError(ValueError):
    """Raised when a package spec looks like it could be shell-unsafe."""


def _validate_spec(spec: str) -> None:
    if not spec or not _SAFE_SPEC_RE.match(spec):
        raise UnsafePackageSpecError(f"Rejected potentially unsafe package spec: {spec!r}")


class PackageManager:
    """Performs pip install/uninstall/upgrade against a target interpreter."""

    def _run_pip(
        self, interpreter: PythonInterpreter, args: list[str], timeout: float = 300.0
    ) -> subprocess.CompletedProcess[str]:
        cmd = [str(interpreter.executable), "-m", "pip", *args]
        logger.info("Running: %s", " ".join(cmd))
        return subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            creationflags=subprocess.CREATE_NO_WINDOW if IS_WINDOWS else 0,
        )

    def install(
        self, interpreter: PythonInterpreter, spec: str, upgrade: bool = False
    ) -> OperationResult:
        """Install (or upgrade) a package spec, e.g. 'requests==2.31.0'."""
        _validate_spec(spec)
        args = ["install", spec]
        if upgrade:
            args.insert(1, "--upgrade")
        try:
            result = self._run_pip(interpreter, args)
        except (OSError, subprocess.SubprocessError) as exc:
            return OperationResult(success=False, message=str(exc), package_name=spec)

        success = result.returncode == 0
        message = result.stdout.strip() if success else result.stderr.strip()
        return OperationResult(
            success=success,
            message=message or ("Installed successfully" if success else "Install failed"),
            package_name=spec,
            returncode=result.returncode,
        )

    def uninstall(self, interpreter: PythonInterpreter, package_name: str) -> OperationResult:
        """Uninstall a package by name (non-interactive, auto-confirm)."""
        _validate_spec(package_name)
        try:
            result = self._run_pip(interpreter, ["uninstall", "-y", package_name])
        except (OSError, subprocess.SubprocessError) as exc:
            return OperationResult(success=False, message=str(exc), package_name=package_name)

        success = result.returncode == 0
        message = result.stdout.strip() if success else result.stderr.strip()
        return OperationResult(
            success=success,
            message=message or ("Uninstalled successfully" if success else "Uninstall failed"),
            package_name=package_name,
            returncode=result.returncode,
        )

    def upgrade(self, interpreter: PythonInterpreter, package_name: str) -> OperationResult:
        """Upgrade a single package to its latest version."""
        return self.install(interpreter, package_name, upgrade=True)

    def upgrade_pip(self, interpreter: PythonInterpreter) -> OperationResult:
        """Upgrade pip itself for the target interpreter."""
        try:
            result = self._run_pip(interpreter, ["install", "--upgrade", "pip"])
        except (OSError, subprocess.SubprocessError) as exc:
            return OperationResult(success=False, message=str(exc), package_name="pip")

        success = result.returncode == 0
        message = result.stdout.strip() if success else result.stderr.strip()
        return OperationResult(
            success=success,
            message=message,
            package_name="pip",
            returncode=result.returncode,
        )

    def freeze(self, interpreter: PythonInterpreter) -> list[str]:
        """Return `pip freeze` output as a list of requirement lines."""
        try:
            result = self._run_pip(interpreter, ["freeze"])
        except (OSError, subprocess.SubprocessError) as exc:
            logger.warning("pip freeze failed: %s", exc)
            return []
        if result.returncode != 0:
            return []
        return [line for line in result.stdout.splitlines() if line.strip()]
