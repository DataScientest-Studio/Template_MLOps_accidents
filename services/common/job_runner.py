"""
Reusable job runner with streaming logs.

Runs a sync callable in a thread, captures log records (filtered by prefix),
and periodically updates the job store with the current log lines so the API
and frontend can show live progress. Use from data service, train service,
or any other service that runs long-running jobs.
"""

import asyncio
import logging
from typing import Any, Callable, List, Optional, Tuple

from services.common.job_store import job_store


def _install_log_capture(
    log_lines: List[str], log_prefixes: Tuple[str, ...]
) -> logging.Handler:
    """Install a root-logger handler that appends formatted records to log_lines (filtered by prefix)."""
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")

    class PrefixFilter(logging.Filter):
        def filter(self, record):
            return any(record.name.startswith(p) for p in log_prefixes)

    class ListHandler(logging.Handler):
        def emit(self, record):
            try:
                log_lines.append(self.format(record))
            except Exception:  # pylint: disable=broad-except
                self.handleError(record)

    handler = ListHandler()
    handler.setFormatter(formatter)
    handler.addFilter(PrefixFilter())
    root = logging.getLogger()
    root.addHandler(handler)
    return handler


def _uninstall_log_capture(handler: logging.Handler) -> None:
    """Remove the given handler from the root logger."""
    logging.getLogger().removeHandler(handler)


async def run_sync_with_streaming_logs(
    job_id: str,
    sync_fn: Callable[..., Any],
    *args: Any,
    log_prefixes: Tuple[str, ...] = ("src.",),
    update_interval_seconds: float = 2.0,
    **kwargs: Any,
) -> Tuple[Optional[Any], Optional[Exception]]:
    """
    Run a sync callable in a thread, capture logs, and periodically push them to the job store.

    Logs are updated in the job store every update_interval_seconds so the API/frontend
    can show live progress. If update_interval_seconds is 0 or None, logs are only
    written once at the end (no streaming).

    Args:
        job_id: Job ID to update with logs.
        sync_fn: Sync callable to run (e.g. preprocess_data, run_training).
        *args: Positional arguments for sync_fn.
        log_prefixes: Logger name prefixes to capture (e.g. ("src.", "services.data_service.")).
        update_interval_seconds: How often to push logs to the job store (seconds). 0 or None = only at end.
        **kwargs: Keyword arguments for sync_fn.

    Returns:
        (result, None) on success, (None, exception) on failure.
        Caller should then call job_store.update_job(job_id, status=..., result=... or error=...) with final state.
    """
    log_lines: List[str] = []
    handler = _install_log_capture(log_lines, log_prefixes)
    try:
        task = asyncio.create_task(asyncio.to_thread(sync_fn, *args, **kwargs))

        if update_interval_seconds and update_interval_seconds > 0:
            while not task.done():
                await asyncio.sleep(update_interval_seconds)
                await job_store.update_job(job_id, logs=list(log_lines))

        # One final push so we have all logs including the last few lines
        await job_store.update_job(job_id, logs=list(log_lines))

        try:
            result = task.result()
            return (result, None)
        except Exception as exc:  # pylint: disable=broad-except
            return (None, exc)
    finally:
        _uninstall_log_capture(handler)
