"""Guard cascade orchestrator — UNIFIED_DESIGN §3.2.

Pipeline: L0 rules → L1 classifier → (optional) L2 LLM judge.
- L0 hit: short-circuit BLOCK (no L1 forward pass).
- L1 score >= thresholds.block: BLOCK.
- L1 score <= thresholds.safe: ALLOW.
- Borderline (between safe/block):
    L2 enabled  → call judge, follow its verdict
    L2 disabled → ALLOW (cheap path) — Eunjin's BufferManager may HOLD-and-rescan
                  with overlap if the buffer is still partial; that's outside this layer.

The engine is stateless w.r.t. session — caller supplies the text to classify.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Any

from stream_shield.guard import rules
from stream_shield.guard.classifier import L1Classifier
from stream_shield.guard.decision import Action, Decision, Verdict
from stream_shield.policy import Policy

logger = logging.getLogger(__name__)


@dataclass
class CascadeResult:
    """Internal trace of every layer that ran. Useful for the dashboard."""
    l0: Verdict
    l1: Verdict | None = None
    l2: Verdict | None = None
    total_ms: float = 0.0


class GuardEngine:
    def __init__(self, policy: Policy, *, l1: L1Classifier | None = None, l2: Any | None = None):
        self.policy = policy
        self.compiled_rules = rules.compile_rules(policy)
        self.l1 = l1 or L1Classifier(policy)
        self.l2 = l2  # optional — guard/llm_judge.py (stretch); duck-typed `async judge(text) -> Verdict`
        self._warm = False

    async def warmup(self) -> None:
        if self._warm:
            return
        try:
            await self.l1.warmup()
        except Exception:
            logger.exception("L1 warmup failed — engine will run in L0-only degraded mode")
        self._warm = True

    async def classify(self, text: str) -> Decision:
        """Run the cascade. Returns Decision with action set."""
        t0 = time.perf_counter()
        trace = CascadeResult(l0=rules.scan(text, self.compiled_rules))
        if trace.l0.label == "malicious":
            return self._finalize(Action.BLOCK, trace, t0, primary=trace.l0)

        try:
            trace.l1 = await self.l1.score(text)
        except Exception as e:
            logger.exception("L1 inference failed")
            # Degrade gracefully: if L0 said safe and L1 broken, allow.
            return self._finalize(
                Action.ALLOW, trace, t0,
                primary=Verdict(score=0.0, label="safe", layer="L1",
                                reason=f"L1 unavailable ({type(e).__name__}): falling back to L0"),
            )

        thr = self.policy.thresholds
        if trace.l1.score >= thr.block:
            return self._finalize(Action.BLOCK, trace, t0, primary=trace.l1)
        if trace.l1.score <= thr.safe:
            return self._finalize(Action.ALLOW, trace, t0, primary=trace.l1)

        # Borderline.
        if self.policy.guard.l2_judge_enabled and self.l2 is not None:
            try:
                trace.l2 = await self.l2.judge(text)
            except Exception:
                logger.exception("L2 judge failed — defaulting borderline → ALLOW")
                return self._finalize(Action.ALLOW, trace, t0, primary=trace.l1)
            action = Action.BLOCK if trace.l2.label == "malicious" else Action.ALLOW
            return self._finalize(action, trace, t0, primary=trace.l2)

        return self._finalize(Action.ALLOW, trace, t0, primary=trace.l1)

    def _finalize(
        self, action: Action, trace: CascadeResult, t0: float, *, primary: Verdict,
    ) -> Decision:
        trace.total_ms = round((time.perf_counter() - t0) * 1000, 2)
        return Decision(
            action=action,
            verdict=primary,
            reason=primary.reason,
            score=primary.score,
            forward={"trace": {
                "l0": _verdict_dict(trace.l0),
                "l1": _verdict_dict(trace.l1),
                "l2": _verdict_dict(trace.l2),
                "total_ms": trace.total_ms,
            }},
        )


def _verdict_dict(v: Verdict | None) -> dict[str, Any] | None:
    if v is None:
        return None
    return {
        "layer": v.layer,
        "label": v.label,
        "score": round(v.score, 4),
        "reason": v.reason,
        **({"extra": v.extra} if v.extra else {}),
    }
