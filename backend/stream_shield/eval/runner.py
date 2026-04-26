"""Eval runner — loads attackset.yaml, runs guard pipeline, emits Report.

Until Dohoon's L1 classifier lands, this runner ships a minimal regex-based
classifier (`l0_only_classifier`) so per-entity policy + metrics can be
demoed end-to-end. Swap in a real classifier via the `classify` argument.

Usage:
    python -m stream_shield.eval.runner --policy default
    python -m stream_shield.eval.runner --policy hospital --json out.json
"""

from __future__ import annotations

import argparse
import json
import re
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

import yaml

from ..guard.decision import Action
from ..guard.normalizer import normalize
from ..metrics import Report, Sample, summarize
from ..policy import Policy, load_policy

ATTACKSET = Path(__file__).resolve().parents[2] / "datasets" / "attackset.yaml"


Classifier = Callable[[str, Policy], tuple[Action, float]]


def l0_only_classifier(text: str, policy: Policy) -> tuple[Action, float]:
    """Regex-only stand-in for the real L0+L1 cascade.

    Returns BLOCK with score 1.0 on any block_phrase / role_spoof_regex hit,
    otherwise ALLOW with 0.0. Replace once `guard/engine.py` is wired.
    """
    norm = normalize(text)
    for pattern in policy.block_phrases:
        if re.search(pattern, norm, flags=re.IGNORECASE):
            return Action.BLOCK, 1.0
    for pattern in policy.role_spoof_regex:
        if re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE):
            return Action.BLOCK, 1.0
    return Action.ALLOW, 0.0


def _flatten(item: Any) -> str:
    """split_stream entries are lists of chunks — concatenate for single-pass eval."""
    if isinstance(item, list):
        return "".join(item)
    return str(item)


def _iter_dataset(raw: dict[str, Any]):
    """Yield (text, is_attack, category, language) tuples from attackset.yaml.

    Categories may be either:
      * dict[lang -> list[str]]     (per-language)
      * list[str | list[str]]       (mixed/unknown language; chunked entries flattened)
    """
    for lang, items in (raw.get("benign") or {}).items():
        for text in items or []:
            yield _flatten(text), False, "benign", lang
    for category, body in (raw.get("attacks") or {}).items():
        if isinstance(body, dict):
            for lang, items in body.items():
                for text in items or []:
                    yield _flatten(text), True, category, lang
        elif isinstance(body, list):
            for text in body:
                yield _flatten(text), True, category, "mixed"


def run(
    policy: Policy,
    *,
    dataset_path: Path = ATTACKSET,
    classify: Classifier = l0_only_classifier,
) -> Report:
    raw = yaml.safe_load(dataset_path.read_text(encoding="utf-8")) or {}
    samples: list[Sample] = []
    for text, is_attack, category, language in _iter_dataset(raw):
        t0 = time.perf_counter()
        action, score = classify(text, policy)
        latency_ms = (time.perf_counter() - t0) * 1000.0
        samples.append(
            Sample(
                text=text,
                is_attack=is_attack,
                category=category,
                language=language,
                action=action,
                score=score,
                latency_ms=latency_ms,
            )
        )
    return summarize(samples)


def _format_report(policy_id: str, report: Report) -> str:
    d = report.as_dict()
    lines = [
        f"=== Stream Shield eval — policy={policy_id} ===",
        f"n_total={d['n_total']}  n_attack={d['n_attack']}  n_benign={d['n_benign']}",
        f"recall={d['recall']:.4f}  fpr={d['fpr']:.4f}",
        f"latency_ms p50={d['latency_ms']['p50']}  p95={d['latency_ms']['p95']}  p99={d['latency_ms']['p99']}",
        "",
        "by_category:",
    ]
    for cat, stat in d["by_category"].items():
        lines.append(f"  {cat:<24} n={stat['n']:>3}  blocked={stat['blocked']:>3}  block_rate={stat['block_rate']:.4f}")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--policy", default="default", help="policy id (default | hospital | fintech)")
    ap.add_argument("--dataset", default=str(ATTACKSET))
    ap.add_argument("--json", dest="json_out", default=None, help="write Report json to this path")
    args = ap.parse_args()

    policy = load_policy(args.policy)
    report = run(policy, dataset_path=Path(args.dataset))
    print(_format_report(policy.policy_id, report))
    if args.json_out:
        Path(args.json_out).write_text(json.dumps(report.as_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
