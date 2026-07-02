"""
main.py

Entry point for PyPackage Manager Pro.

Run with:
    python main.py
"""

from __future__ import annotations

import sys
import traceback
from tkinter import messagebox

from gui.app import App
from utils.logger import get_logger, setup_logging

logger = get_logger(__name__)


def main() -> int:
    setup_logging()
    logger.info("Starting PyPackage Manager Pro")

    try:
        app = App()
        app.protocol("WM_DELETE_WINDOW", app.on_close)
        app.mainloop()
    except Exception as exc:  # noqa: BLE001 - top-level safety net
        logger.critical("Unhandled exception: %s", exc)
        logger.critical(traceback.format_exc())
        try:
            messagebox.showerror(
                "PyPackage Manager Pro - Fatal Error",
                f"A fatal error occurred and the application must close:\n\n{exc}",
            )
        except Exception:
            pass
        return 1

    logger.info("PyPackage Manager Pro closed normally")
    return 0


if __name__ == "__main__":
    sys.exit(main())
