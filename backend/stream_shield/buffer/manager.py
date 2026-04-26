"""Buffer Manager — classifies transcript during auto-response.

Architecture (VAD-respecting):
- Classifier runs during Gemini's auto-response phase
- By the time auto-response turnComplete arrives, classifier is done
- Server decides: safe → send clientContent, blocked → notify client

See UNIFIED_DESIGN.md §3.2.
"""

from __future__ import annotations

import logging

from stream_shield.guard.decision import Decision, Action
from stream_shield.guard.engine import GuardEngine
from stream_shield.policy import Policy
from stream_shield.session import ShieldSession

logger = logging.getLogger(__name__)


class BufferManager:
    def __init__(self, guard: GuardEngine, policy: Policy) -> None:
        self.guard = guard
        self.policy = policy

    async def classify(self, session: ShieldSession, transcript: str) -> Decision:
        """Classify transcript. Called as background task during auto-response."""
        verdict = await self.guard.classify(transcript)
        session.scores.append(verdict.score)
        session.total_turns += 1

        if verdict.score >= self.policy.thresholds.block:
            return Decision(
                action=Action.BLOCK,
                verdict=verdict,
                reason=verdict.reason,
                score=verdict.score,
            )

        return Decision(
            action=Action.ALLOW,
            verdict=verdict,
            score=verdict.score,
        )
