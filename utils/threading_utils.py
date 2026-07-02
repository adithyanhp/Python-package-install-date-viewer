"""
utils/threading_utils.py

Small helper around ThreadPoolExecutor so GUI code never blocks the
Tkinter main loop. GUI callbacks scheduled from worker threads must go
through Tk's `.after()` - this helper provides a convenient wrapper.
"""

from __future__ import annotations

from concurrent.futures import Future, ThreadPoolExecutor
from typing import Any, Callable

from utils.logger import get_logger

logger = get_logger(__name__)


class BackgroundTaskRunner:
    """
    Wraps a ThreadPoolExecutor and a Tk widget so that results/errors
    from background work are safely marshalled back onto the UI thread
    via `widget.after(0, ...)`.
    """

    def __init__(self, max_workers: int = 4) -> None:
        self._executor = ThreadPoolExecutor(
            max_workers=max_workers, thread_name_prefix="PPMPWorker"
        )

    def run(
        self,
        tk_widget: Any,
        work_fn: Callable[..., Any],
        on_success: Callable[[Any], None] | None = None,
        on_error: Callable[[BaseException], None] | None = None,
        *args: Any,
        **kwargs: Any,
    ) -> Future:
        """
        Execute `work_fn(*args, **kwargs)` on a worker thread. When it
        completes, `on_success`/`on_error` are invoked on the Tk main
        thread via `tk_widget.after(0, ...)`.
        """

        def _safe_after(callback: Callable[[], None]) -> None:
            try:
                tk_widget.after(0, callback)
            except RuntimeError:
                # Window was already closed/destroyed before the background
                # task finished - nothing sensible left to update.
                logger.debug("Dropped background task result: widget destroyed")

        def _done_callback(future: Future) -> None:
            try:
                result = future.result()
            except BaseException as exc:  # noqa: BLE001 - surfaced to UI
                logger.exception("Background task failed: %s", exc)
                if on_error is not None:
                    _safe_after(lambda: on_error(exc))
                return
            if on_success is not None:
                _safe_after(lambda: on_success(result))

        future = self._executor.submit(work_fn, *args, **kwargs)
        future.add_done_callback(_done_callback)
        return future

    def shutdown(self, wait: bool = False) -> None:
        self._executor.shutdown(wait=wait, cancel_futures=True)
