"""Async task queue with bounded concurrency and per-task timeout."""
from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable

import structlog

log = structlog.get_logger(__name__)


class TaskQueue:
    """Bounded worker pool. Each submitted coroutine runs under a timeout."""

    def __init__(self, max_concurrent: int, task_timeout_sec: int) -> None:
        self._sem = asyncio.Semaphore(max_concurrent)
        self._timeout = task_timeout_sec
        self._tasks: set[asyncio.Task] = set()

    def submit(
        self,
        coro_factory: Callable[[], Awaitable[None]],
        *,
        name: str,
        on_error: Callable[[str], Awaitable[None]] | None = None,
    ) -> None:
        """Schedule work; returns immediately (fire-and-forget).

        ``on_error`` is awaited with "timeout" or "failed" if the task does not
        complete cleanly, so the caller can notify the user.
        """
        task = asyncio.create_task(self._run(coro_factory, name, on_error), name=name)
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)

    async def _run(
        self,
        coro_factory: Callable[[], Awaitable[None]],
        name: str,
        on_error: Callable[[str], Awaitable[None]] | None,
    ) -> None:
        async with self._sem:
            log.info("task_start", task=name)
            reason: str | None = None
            try:
                await asyncio.wait_for(coro_factory(), timeout=self._timeout)
                log.info("task_done", task=name)
            except asyncio.TimeoutError:
                log.error("task_timeout", task=name, timeout=self._timeout)
                reason = "timeout"
            except Exception:
                log.exception("task_failed", task=name)
                reason = "failed"
        if reason and on_error is not None:
            try:
                await on_error(reason)
            except Exception:
                log.exception("task_on_error_failed", task=name)

    async def drain(self) -> None:
        """Await all in-flight tasks (used on shutdown)."""
        if self._tasks:
            await asyncio.gather(*list(self._tasks), return_exceptions=True)
