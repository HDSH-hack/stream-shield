"""L1 classifier — Prompt Guard 2 86M wrapper.

Stub: Dohoon이 transformers pipeline으로 구현 예정.
See UNIFIED_DESIGN.md §2.2 D3.
"""

from __future__ import annotations

import logging

from stream_shield.guard.decision import Verdict
from stream_shield.policy import Policy

logger = logging.getLogger(__name__)


class L1Classifier:
    def __init__(self, policy: Policy) -> None:
        self.policy = policy
        self.model_name = policy.guard.primary_model
        self._pipeline = None

    async def load(self) -> None:
        """Load the transformers model. Raises if unavailable."""
        # TODO(dohoon): implement actual model loading
        # from transformers import pipeline
        # self._pipeline = pipeline(
        #     "text-classification",
        #     model=self.model_name,
        #     max_length=self.policy.guard.max_length,
        #     truncation=True,
        # )
        raise NotImplementedError("L1 classifier not yet implemented — L0-only mode")

    async def classify(self, text: str) -> Verdict:
        """Classify text using Prompt Guard 2."""
        if self._pipeline is None:
            return Verdict(score=0.0, label="safe", layer="L1", reason="model not loaded")

        # TODO(dohoon): actual inference
        return Verdict(score=0.0, label="safe", layer="L1", reason="stub")
