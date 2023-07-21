""""Class to handle futures."""
from __future__ import annotations

from asyncio import Future
from typing import Any

import async_timeout


class ZagonelFuture:
    """"Class to handle futures."""

    def __init__(self):
        """"Init future."""
        self.fut: Future = Future()
        self.loop = self.fut.get_loop()

    def _resolve(self, item: Any) -> None:
        """"Resolve future."""
        if not self.fut.cancelled():
            self.fut.set_result(item)

    def resolve(self, item: Any) -> None:
        """"Resolve future."""
        self.loop.call_soon_threadsafe(self._resolve, item)

    async def async_get(self, timeout: float | int) -> Any:
        """"Retrieve future."""
        try:
            async with async_timeout.timeout(timeout):
                return await self.fut
        finally:
            self.fut.cancel()
