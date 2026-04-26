"""Tiered guard engine — L0 rules -> L1 classifier -> L2 LLM judge.

See UNIFIED_DESIGN.md §2.2 D3.
"""

from __future__ import annotations

import logging
import time

from stream_shield.guard.decision import Verdict
from stream_shield.guard.normalizer import normalize
from stream_shield.guard.rules import L0Rules
from stream_shield.policy import Policy

logger = logging.getLogger(__name__)


class GuardEngine:
    def __init__(self, policy: Policy) -> None:
        self.policy = policy
        self.l0 = L0Rules(policy)
        self._classifier = None  # L1: loaded on warmup

    async def warmup(self) -> None:
        """Pre-load L1 classifier model."""
        try:
            from stream_shield.guard.classifier import L1Classifier
            self._classifier = L1Classifier(self.policy)
            await self._classifier.load()
            logger.info("L1 classifier loaded: %s", self.policy.guard.primary_model)
        except Exception as e:
            logger.warning("L1 classifier not available, L0-only mode: %s", e)
            self._classifier = None

    async def classify(self, text: str) -> Verdict:
        """Run tiered classification: L0 -> L1 -> (L2 stretch)."""
        t0 = time.monotonic()

        # L0 — rule pass (<1ms)
        hit = self.l0.check(text)
        if hit.matched:
            latency = (time.monotonic() - t0) * 1000
            logger.info("L0 BLOCK: rule=%s pattern=%r (%.1fms)", hit.rule, hit.pattern, latency)
            return Verdict(
                score=1.0,
                label="malicious",
                layer="L0",
                reason=f"{hit.rule}: {hit.pattern}",
                extra={"latency_ms": round(latency, 1)},
            )

        # L1 — classifier
        if self._classifier is not None:
            normalized = normalize(text)
            verdict = await self._classifier.classify(normalized)
            latency = (time.monotonic() - t0) * 1000
            verdict.extra["latency_ms"] = round(latency, 1)
            logger.info("L1 result: score=%.3f label=%s (%.1fms)", verdict.score, verdict.label, latency)
            return verdict

        # No classifier available — pass through
        latency = (time.monotonic() - t0) * 1000
        return Verdict(
            score=0.0,
            label="safe",
            layer="L0-only",
            reason="no L1 classifier loaded",
            extra={"latency_ms": round(latency, 1)},
        )
