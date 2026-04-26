"""Response Buffer — holds modelTurn chunks while classifier runs.

State machine:
  BUFFERING → FLUSHING  (classifier says safe)
  BUFFERING → DROPPED   (classifier says block)

See UNIFIED_DESIGN.md §2.2 D2 / §3.2.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class BufferState(str, Enum):
    BUFFERING = "BUFFERING"
    FLUSHING = "FLUSHING"
    DROPPED = "DROPPED"


@dataclass
class ResponseBuffer:
    state: BufferState = BufferState.BUFFERING
    queue: list[dict] = field(default_factory=list)
    _flush_event: asyncio.Event = field(default_factory=asyncio.Event)

    def enqueue(self, server_event: dict) -> None:
        """Buffer a modelTurn chunk while classifier is running."""
        if self.state == BufferState.BUFFERING:
            self.queue.append(server_event)
        # FLUSHING / DROPPED: handled by caller checking state

    def flush(self) -> list[dict]:
        """Mark safe — return buffered chunks and switch to FLUSHING."""
        self.state = BufferState.FLUSHING
        chunks = list(self.queue)
        self.queue.clear()
        self._flush_event.set()
        logger.info("response buffer: FLUSH (%d chunks)", len(chunks))
        return chunks

    def drain(self) -> list[dict]:
        """Return and clear any remaining buffered chunks (after flush)."""
        chunks = list(self.queue)
        self.queue.clear()
        return chunks

    def drop(self) -> None:
        """Mark blocked — discard buffered chunks."""
        dropped = len(self.queue)
        self.queue.clear()
        self.state = BufferState.DROPPED
        self._flush_event.set()
        logger.info("response buffer: DROP (%d chunks discarded)", dropped)

    def reset(self) -> None:
        """Reset for next turn."""
        self.queue.clear()
        self.state = BufferState.BUFFERING
        self._flush_event = asyncio.Event()

    async def wait_for_verdict(self, timeout: float | None = None) -> BufferState:
        """Wait until flush() or drop() is called."""
        try:
            await asyncio.wait_for(self._flush_event.wait(), timeout=timeout)
        except asyncio.TimeoutError:
            # Timeout → assume safe, flush
            logger.warning("response buffer: verdict timeout, auto-flushing")
            self.flush()
        return self.state
