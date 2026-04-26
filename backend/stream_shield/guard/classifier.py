"""L1 prompt-injection classifier wrapper — UNIFIED_DESIGN §3.2.

Wraps a HuggingFace AutoModelForSequenceClassification (Prompt Guard 2,
ProtectAI DeBERTa, etc.) behind a uniform `score(text) -> Verdict` API.

Inference is sync inside the model; the public API is `async` and offloads
the actual forward pass to a thread so it doesn't stall the event loop.
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

from stream_shield.guard.decision import Verdict
from stream_shield.guard.normalizer import normalize
from stream_shield.policy import Policy

logger = logging.getLogger(__name__)


_MAL_LABEL_NAMES = {"injection", "label_1", "malicious", "unsafe", "jailbreak"}


class L1Classifier:
    """Single-model L1 scorer. Async-friendly via `asyncio.to_thread`."""

    def __init__(self, policy: Policy):
        self.policy = policy
        self.model_id = policy.guard.primary_model
        self.max_length = policy.guard.max_length
        self.runtime = policy.guard.runtime
        self._tok: Any | None = None
        self._mdl: Any | None = None
        self._mal_idx: int = 1
        self._loaded = False

    def _load(self) -> None:
        if self._loaded:
            return
        if self.runtime != "transformers":
            raise NotImplementedError(
                f"runtime={self.runtime!r} not yet supported; use 'transformers'"
            )
        # Heavy imports are deferred so module import stays cheap.
        from transformers import AutoModelForSequenceClassification, AutoTokenizer
        import torch  # noqa: F401 — surfaces missing-dep error here, not later

        logger.info("loading L1 model: %s", self.model_id)
        self._tok = AutoTokenizer.from_pretrained(self.model_id)
        # low_cpu_mem_usage=False forces eager weight loading. Without this,
        # newer transformers leave the classifier head on the 'meta' device,
        # causing 'Tensor on device meta is not on the expected device cpu!'
        # at inference time.
        self._mdl = AutoModelForSequenceClassification.from_pretrained(
            self.model_id,
            low_cpu_mem_usage=False,
        )
        self._mdl.to("cpu")
        self._mdl.eval()

        id2label = self._mdl.config.id2label
        for i, lbl in id2label.items():
            if str(lbl).lower() in _MAL_LABEL_NAMES:
                self._mal_idx = int(i)
                break
        else:
            self._mal_idx = max(int(k) for k in id2label.keys())
        self._loaded = True

    async def warmup(self) -> None:
        await asyncio.to_thread(self._load)
        await self.score("warmup")

    async def score(self, text: str) -> Verdict:
        if not text:
            return Verdict(score=0.0, label="safe", layer="L1", reason="empty")
        if not self._loaded:
            await asyncio.to_thread(self._load)
        norm = normalize(text)
        return await asyncio.to_thread(self._score_sync, norm)

    def _score_sync(self, text: str) -> Verdict:
        import torch

        t0 = time.perf_counter()
        with torch.no_grad():
            enc = self._tok(  # type: ignore[misc]
                text, return_tensors="pt", truncation=True, max_length=self.max_length,
            )
            logits = self._mdl(**enc).logits[0]  # type: ignore[misc]
            probs = torch.softmax(logits, dim=-1)
            score = float(probs[self._mal_idx])
        elapsed_ms = (time.perf_counter() - t0) * 1000

        thr = self.policy.thresholds
        if score >= thr.block:
            label = "malicious"
        elif score <= thr.safe:
            label = "safe"
        else:
            label = "suspicious"

        return Verdict(
            score=score,
            label=label,
            layer="L1",
            reason=f"{self.model_id} p_malicious={score:.3f}",
            extra={"latency_ms": round(elapsed_ms, 2), "model": self.model_id},
        )
