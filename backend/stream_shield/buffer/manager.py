"""Buffer Manager — classifies transcripts before forwarding to Gemini.

Hold-and-scan architecture:
1. Receive inputTranscription (STT) from Gemini auto-VAD
2. Run guard engine (L0 rules → L1 classifier)
3. Return decision: ALLOW → server sends text to Gemini for response
                     BLOCK → server drops, notifies client

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

    async def classify_transcript(self, session: ShieldSession, transcript: str) -> Decision:
        """Classify transcript and return decision."""
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
