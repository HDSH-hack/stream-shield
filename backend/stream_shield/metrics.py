"""Eval metrics — recall / FPR / latency percentiles.

UNIFIED_DESIGN §6 (eval). Pure functions over decision logs; the runner produces
the inputs from `datasets/attackset.yaml`.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from .guard.decision import Action


@dataclass
class Sample:
    text: str
    is_attack: bool
    category: str          # benign | direct_injection | jailbreak | ...
    language: str          # ko | en
    action: Action
    score: float
    latency_ms: float


@dataclass
class CategoryStat:
    name: str
    n: int = 0
    blocked: int = 0       # action == BLOCK
    held: int = 0          # action == HOLD

    @property
    def block_rate(self) -> float:
        return self.blocked / self.n if self.n else 0.0


@dataclass
class Report:
    n_total: int
    n_attack: int
    n_benign: int
    recall: float          # attacks blocked / attacks
    fpr: float             # benign blocked  / benign
    p50_ms: float
    p95_ms: float
    p99_ms: float
    by_category: dict[str, CategoryStat] = field(default_factory=dict)

    def as_dict(self) -> dict:
        return {
            "n_total": self.n_total,
            "n_attack": self.n_attack,
            "n_benign": self.n_benign,
            "recall": round(self.recall, 4),
            "fpr": round(self.fpr, 4),
            "latency_ms": {
                "p50": round(self.p50_ms, 2),
                "p95": round(self.p95_ms, 2),
                "p99": round(self.p99_ms, 2),
            },
            "by_category": {
                k: {"n": v.n, "blocked": v.blocked, "block_rate": round(v.block_rate, 4)}
                for k, v in self.by_category.items()
            },
        }


def _percentile(values: list[float], q: float) -> float:
    if not values:
        return 0.0
    s = sorted(values)
    # nearest-rank
    k = max(0, min(len(s) - 1, math.ceil(q * len(s)) - 1))
    return s[k]


def summarize(samples: list[Sample]) -> Report:
    n_attack = sum(1 for s in samples if s.is_attack)
    n_benign = len(samples) - n_attack

    attack_blocked = sum(1 for s in samples if s.is_attack and s.action == Action.BLOCK)
    benign_blocked = sum(1 for s in samples if not s.is_attack and s.action == Action.BLOCK)

    by_cat: dict[str, CategoryStat] = {}
    for s in samples:
        st = by_cat.setdefault(s.category, CategoryStat(name=s.category))
        st.n += 1
        if s.action == Action.BLOCK:
            st.blocked += 1
        elif s.action == Action.HOLD:
            st.held += 1

    latencies = [s.latency_ms for s in samples]
    return Report(
        n_total=len(samples),
        n_attack=n_attack,
        n_benign=n_benign,
        recall=attack_blocked / n_attack if n_attack else 0.0,
        fpr=benign_blocked / n_benign if n_benign else 0.0,
        p50_ms=_percentile(latencies, 0.50),
        p95_ms=_percentile(latencies, 0.95),
        p99_ms=_percentile(latencies, 0.99),
        by_category=by_cat,
    )
