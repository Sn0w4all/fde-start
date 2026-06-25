"""Retry with exponential backoff for flaky network/API calls."""
from __future__ import annotations

import asyncio
import random
from collections.abc import Awaitable, Callable
from typing import TypeVar

import logging

logger = logging.getLogger(__name__)

T = TypeVar("T")


async def with_backoff(
    fn: Callable[[], Awaitable[T]],
    *,
    attempts: int = 4,
    base_delay: float = 1.0,
    max_delay: float = 20.0,
    exc_types: tuple[type[BaseException], ...] = (Exception,),
) -> T:
    """Call ``fn`` retrying on ``exc_types`` with exponential backoff + jitter."""
    last: BaseException | None = None
    for i in range(attempts):
        try:
            return await fn()
        except exc_types as exc:  # noqa: PERF203
            last = exc
            if i == attempts - 1:
                break
            delay = min(max_delay, base_delay * (2**i)) + random.uniform(0, 0.5)
            logger.warning("retrying attempt %d/%d failed because of %s",i + 1, attempts, str(exc))
            await asyncio.sleep(delay)
            
    raise last
   