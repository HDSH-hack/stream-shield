"""Tiered guard engine — L0 rules -> L1 classifier -> L2 LLM judge.

Stub for Phase 0. Full implementation in Phase 1.
See UNIFIED_DESIGN.md §2.2 D3.
"""

from __future__ import annotations

from stream_shield.guard.decision import Verdict
from stream_shield.policy import Policy


class GuardEngine:
    def __init__(self, policy: Policy) -> None:
        self.policy = policy

    async def warmup(self) -> None:
        """Pre-load models. No-op in Phase 0 stub."""

    async def classify(self, text: str) -> Verdict:
        """Classify text. Returns safe verdict in Phase 0 stub."""
        return Verdict(score=0.0, label="safe", layer="stub", reason="phase0-stub")
