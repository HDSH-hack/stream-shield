"""Buffer Manager — Hold->Scan->Release + Response Buffer.

Stub for Phase 0. Full implementation in Phase 1.
See UNIFIED_DESIGN.md §3.2.
"""

from __future__ import annotations

from stream_shield.guard.engine import GuardEngine
from stream_shield.policy import Policy


class BufferManager:
    def __init__(self, guard: GuardEngine, policy: Policy) -> None:
        self.guard = guard
        self.policy = policy
