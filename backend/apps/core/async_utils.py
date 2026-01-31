# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Async utilities for running async code from sync contexts.

Provides helpers to safely run async coroutines from synchronous views
when Django is running in ASGI mode with an existing event loop.
"""
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Coroutine, TypeVar

T = TypeVar("T")

# Thread pool for running async code from sync context
_executor = ThreadPoolExecutor(max_workers=8)


def run_async(coro: Coroutine[Any, Any, T]) -> T:
    """
    Run an async coroutine from a sync context.

    Handles the case where we're called from within an existing event loop
    (e.g., Django running under ASGI) by running the coroutine in a separate
    thread with its own event loop.

    Args:
        coro: The coroutine to run

    Returns:
        The result of the coroutine

    Raises:
        Any exception raised by the coroutine
    """

    def run_in_thread():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()

    future = _executor.submit(run_in_thread)
    return future.result()
