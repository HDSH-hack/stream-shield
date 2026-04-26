"""Eval harness — feeds attackset.yaml through GuardEngine and reports
recall / FPR / per-category recall / latency p50,p95,p99.

Run:
    cd backend && source .venv/bin/activate
    python -m stream_shield.eval.runner --policy default
    python -m stream_shield.eval.runner --policy hospital --no-l1   # rules-only baseline

The --no-l1 mode is useful when transformers/torch isn't installed yet —
you'll only measure L0 but the wiring is exercised.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import statistics
import sys
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path

import yaml

from stream_shield.guard.decision import Action, Decision
from stream_shield.guard.engine import GuardEngine
from stream_shield.policy import load_policy

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
ATTACKSET_PATH = REPO_ROOT / "datasets" / "attackset.yaml"
RESULTS_DIR = REPO_ROOT / "eval_results"


@dataclass
class Sample:
    text: str
    is_attack: bool
    category: str
    lang: str = ""


@dataclass
class CaseResult:
    category: str
    lang: str
    is_attack: bool
    text: str
    action: str
    score: float
    layer: str
    reason: str
    latency_ms: float


@dataclass
class EvalReport:
    policy_id: str
    n_total: int
    n_attacks: int
    n_benign: int
    recall: float
    fpr: float
    latency_ms_p50: float
    latency_ms_p95: float
    latency_ms_p99: float
    latency_ms_mean: float
    per_category_recall: dict[str, float]
    misses: list[CaseResult] = field(default_factory=list)
    fps: list[CaseResult] = field(default_factory=list)
    cases: list[CaseResult] = field(default_factory=list)


def load_samples(path: Path = ATTACKSET_PATH) -> list[Sample]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    samples: list[Sample] = []

    for lang, items in (raw.get("benign") or {}).items():
        for t in items:
            samples.append(Sample(text=t, is_attack=False, category="benign", lang=lang))

    for cat, content in (raw.get("attacks") or {}).items():
        if isinstance(content, dict):
            for lang, items in content.items():
                for t in items:
                    samples.append(Sample(text=t, is_attack=True, category=cat, lang=lang))
        elif isinstance(content, list):
            for entry in content:
                if isinstance(entry, list):
                    # split_stream chunks → concat; multi_turn_drip turns → newline join.
                    sep = "\n" if cat == "multi_turn_drip" else ""
                    text = sep.join(entry)
                    samples.append(Sample(text=text, is_attack=True, category=cat, lang="multi"))
                else:
                    samples.append(Sample(text=entry, is_attack=True, category=cat, lang="multi"))
    return samples


def percentile(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    s = sorted(values)
    k = max(0, min(len(s) - 1, int(round((p / 100) * (len(s) - 1)))))
    return s[k]


async def evaluate(policy_id: str, *, disable_l1: bool, max_samples: int | None) -> EvalReport:
    policy = load_policy(policy_id)
    engine = GuardEngine(policy)

    if disable_l1:
        # Stub L1 always-safe so the cascade falls through to the "L1 unavailable" path
        # and reports only L0 verdicts.
        from stream_shield.guard.decision import Verdict

        class _StubL1:
            async def warmup(self): pass
            async def score(self, _: str):
                return Verdict(score=0.0, label="safe", layer="L1", reason="L1 disabled (--no-l1)")
        engine.l1 = _StubL1()

    await engine.warmup()

    samples = load_samples()
    if max_samples:
        samples = samples[:max_samples]

    cases: list[CaseResult] = []
    latencies: list[float] = []
    cat_hits: dict[str, list[bool]] = {}
    tp = fp = 0

    for s in samples:
        t0 = time.perf_counter()
        d: Decision = await engine.classify(s.text)
        elapsed = (time.perf_counter() - t0) * 1000
        latencies.append(elapsed)

        is_block = d.action == Action.BLOCK
        cr = CaseResult(
            category=s.category, lang=s.lang, is_attack=s.is_attack, text=s.text,
            action=d.action.value,
            score=round(d.score, 4),
            layer=(d.verdict.layer if d.verdict else ""),
            reason=d.reason,
            latency_ms=round(elapsed, 2),
        )
        cases.append(cr)

        if s.is_attack:
            cat_hits.setdefault(s.category, []).append(is_block)
            if is_block:
                tp += 1
        else:
            if is_block:
                fp += 1

    n_attacks = sum(1 for s in samples if s.is_attack)
    n_benign = sum(1 for s in samples if not s.is_attack)
    per_cat = {c: (sum(h) / len(h) if h else 0.0) for c, h in cat_hits.items()}

    return EvalReport(
        policy_id=policy_id,
        n_total=len(samples),
        n_attacks=n_attacks,
        n_benign=n_benign,
        recall=tp / n_attacks if n_attacks else 0.0,
        fpr=fp / n_benign if n_benign else 0.0,
        latency_ms_p50=percentile(latencies, 50),
        latency_ms_p95=percentile(latencies, 95),
        latency_ms_p99=percentile(latencies, 99),
        latency_ms_mean=statistics.mean(latencies) if latencies else 0,
        per_category_recall=per_cat,
        misses=[c for c in cases if c.is_attack and c.action != "BLOCK"],
        fps=[c for c in cases if (not c.is_attack) and c.action == "BLOCK"],
        cases=cases,
    )


def print_report(r: EvalReport) -> None:
    print(f"\n=== Eval: policy={r.policy_id} | {r.n_total} samples "
          f"({r.n_attacks} attack / {r.n_benign} benign) ===")
    print(f"recall = {r.recall*100:5.1f}%   FPR = {r.fpr*100:5.1f}%   "
          f"latency p50/p95/p99 = {r.latency_ms_p50:.1f} / "
          f"{r.latency_ms_p95:.1f} / {r.latency_ms_p99:.1f} ms "
          f"(mean {r.latency_ms_mean:.1f})")

    print("\nper-category recall:")
    for cat in sorted(r.per_category_recall):
        print(f"  {cat:<28} {r.per_category_recall[cat]*100:5.1f}%")

    if r.misses:
        print(f"\nMISSES ({len(r.misses)}):")
        for m in r.misses:
            head = m.text.replace("\n", " ⏎ ")[:70]
            print(f"  [{m.category}/{m.lang}] action={m.action} score={m.score} "
                  f"layer={m.layer} | {head}")
    if r.fps:
        print(f"\nFALSE POSITIVES ({len(r.fps)}):")
        for m in r.fps:
            head = m.text.replace("\n", " ⏎ ")[:70]
            print(f"  [{m.lang}] action={m.action} score={m.score} layer={m.layer} | {head}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--policy", default="default")
    ap.add_argument("--no-l1", action="store_true", help="Skip L1 inference (rules-only baseline)")
    ap.add_argument("--max-samples", type=int, default=None)
    ap.add_argument("--out", type=Path, default=None,
                    help="Write JSON report (default: eval_results/{policy}_{ts}.json)")
    args = ap.parse_args()

    report = asyncio.run(evaluate(args.policy, disable_l1=args.no_l1,
                                  max_samples=args.max_samples))
    print_report(report)

    out = args.out
    if out is None:
        RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        out = RESULTS_DIR / f"{args.policy}_{int(time.time())}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(asdict(report), ensure_ascii=False, indent=2))
    print(f"\nWritten: {out.relative_to(REPO_ROOT.parent) if out.is_absolute() else out}")


if __name__ == "__main__":
    sys.exit(main())
