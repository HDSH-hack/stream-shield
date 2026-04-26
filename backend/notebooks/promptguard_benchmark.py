"""Prompt-injection classifier benchmark — Phase 0 model selection.

Loads 3–4 candidate L1 models, runs them against the attackset, reports
recall / FPR / latency. Result drives `policy.default.yaml::guard.primary_model`.

Run:
    cd backend && source .venv/bin/activate
    pip install transformers torch  # if not yet
    python -m notebooks.promptguard_benchmark           # all default models
    python -m notebooks.promptguard_benchmark --models protectai/deberta-v3-small-prompt-injection-v2
    python -m notebooks.promptguard_benchmark --device cpu --max-samples 50

Note:
- meta-llama/Llama-Prompt-Guard-2-86M requires HF auth (`huggingface-cli login`).
- ProtectAI DeBERTa models are open access.
"""

from __future__ import annotations

import argparse
import json
import statistics
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import yaml


REPO_ROOT = Path(__file__).resolve().parent.parent
ATTACKSET_PATH = REPO_ROOT / "datasets" / "attackset.yaml"

DEFAULT_MODELS = [
    "meta-llama/Llama-Prompt-Guard-2-86M",
    "protectai/deberta-v3-base-prompt-injection-v2",
    "protectai/deberta-v3-small-prompt-injection-v2",
]


@dataclass
class Sample:
    text: str
    is_attack: bool
    category: str
    lang: str = ""


@dataclass
class ModelResult:
    model_id: str
    n_attacks: int
    n_benign: int
    recall: float                # attack-detection rate
    fpr: float                   # benign-misfire rate
    latency_ms_p50: float
    latency_ms_p95: float
    latency_ms_mean: float
    per_category_recall: dict[str, float]
    misses: list[dict[str, Any]] = field(default_factory=list)
    fps: list[dict[str, Any]] = field(default_factory=list)
    error: str = ""


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
                    text = "".join(entry)
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


def run_model(model_id: str, samples: list[Sample], *, device: str, threshold: float) -> ModelResult:
    """Returns ModelResult — populates `error` instead of raising on load failure."""
    try:
        from transformers import AutoModelForSequenceClassification, AutoTokenizer
        import torch
    except ImportError as e:
        return ModelResult(model_id=model_id, n_attacks=0, n_benign=0,
                           recall=0, fpr=0, latency_ms_p50=0, latency_ms_p95=0, latency_ms_mean=0,
                           per_category_recall={}, error=f"transformers/torch not installed: {e}")

    print(f"\n=== {model_id} ===")
    try:
        tok = AutoTokenizer.from_pretrained(model_id)
        mdl = AutoModelForSequenceClassification.from_pretrained(model_id)
        mdl.eval()
        if device != "cpu":
            mdl = mdl.to(device)
    except Exception as e:
        return ModelResult(model_id=model_id, n_attacks=0, n_benign=0,
                           recall=0, fpr=0, latency_ms_p50=0, latency_ms_p95=0, latency_ms_mean=0,
                           per_category_recall={}, error=f"load failed: {e}")

    # Determine "malicious" label index — meta uses LABEL_1, ProtectAI uses INJECTION
    id2label = mdl.config.id2label
    mal_idx = None
    for i, lbl in id2label.items():
        if str(lbl).lower() in {"injection", "label_1", "malicious", "unsafe", "jailbreak"}:
            mal_idx = int(i)
            break
    if mal_idx is None:
        mal_idx = max(int(k) for k in id2label.keys())  # fallback: highest idx

    latencies: list[float] = []
    misses: list[dict[str, Any]] = []
    fps: list[dict[str, Any]] = []
    cat_hits: dict[str, list[bool]] = {}
    tp = fp = 0

    # warmup
    with torch.no_grad():
        enc = tok("warmup", return_tensors="pt", truncation=True, max_length=512)
        if device != "cpu":
            enc = {k: v.to(device) for k, v in enc.items()}
        mdl(**enc)

    for s in samples:
        with torch.no_grad():
            t0 = time.perf_counter()
            enc = tok(s.text, return_tensors="pt", truncation=True, max_length=512)
            if device != "cpu":
                enc = {k: v.to(device) for k, v in enc.items()}
            logits = mdl(**enc).logits[0]
            probs = torch.softmax(logits, dim=-1)
            score = float(probs[mal_idx])
            elapsed_ms = (time.perf_counter() - t0) * 1000
        latencies.append(elapsed_ms)

        predicted_attack = score >= threshold
        if s.is_attack:
            cat_hits.setdefault(s.category, []).append(predicted_attack)
            if predicted_attack:
                tp += 1
            else:
                misses.append({"category": s.category, "lang": s.lang,
                               "text": s.text, "score": score})
        else:
            if predicted_attack:
                fp += 1
                fps.append({"category": s.category, "lang": s.lang,
                            "text": s.text, "score": score})

    n_attacks = sum(1 for s in samples if s.is_attack)
    n_benign = sum(1 for s in samples if not s.is_attack)
    recall = tp / n_attacks if n_attacks else 0.0
    fpr = fp / n_benign if n_benign else 0.0

    per_cat = {cat: (sum(hits) / len(hits) if hits else 0.0)
               for cat, hits in cat_hits.items()}

    return ModelResult(
        model_id=model_id,
        n_attacks=n_attacks,
        n_benign=n_benign,
        recall=recall,
        fpr=fpr,
        latency_ms_p50=percentile(latencies, 50),
        latency_ms_p95=percentile(latencies, 95),
        latency_ms_mean=statistics.mean(latencies) if latencies else 0,
        per_category_recall=per_cat,
        misses=misses,
        fps=fps,
    )


def print_summary(results: list[ModelResult]) -> None:
    print("\n" + "=" * 78)
    print(f"{'model':<55} {'recall':>7} {'FPR':>6} {'p50ms':>7} {'p95ms':>7}")
    print("-" * 78)
    for r in results:
        if r.error:
            print(f"{r.model_id:<55} ERROR: {r.error[:80]}")
            continue
        print(f"{r.model_id:<55} {r.recall*100:>6.1f}% {r.fpr*100:>5.1f}% "
              f"{r.latency_ms_p50:>6.1f} {r.latency_ms_p95:>6.1f}")
    print("=" * 78)
    for r in results:
        if r.error or not r.per_category_recall:
            continue
        print(f"\n[{r.model_id}] per-category recall:")
        for cat, v in sorted(r.per_category_recall.items()):
            print(f"  {cat:<28} {v*100:>5.1f}%")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", nargs="+", default=DEFAULT_MODELS)
    ap.add_argument("--device", default="cpu", help="cpu | cuda | mps")
    ap.add_argument("--threshold", type=float, default=0.5)
    ap.add_argument("--max-samples", type=int, default=0, help="0 = all")
    ap.add_argument("--out", type=Path, default=REPO_ROOT / "notebooks" / "bench_results.json")
    args = ap.parse_args()

    samples = load_samples()
    if args.max_samples:
        samples = samples[: args.max_samples]
    print(f"Loaded {len(samples)} samples "
          f"({sum(s.is_attack for s in samples)} attack / "
          f"{sum(not s.is_attack for s in samples)} benign)")

    results = [run_model(m, samples, device=args.device, threshold=args.threshold)
               for m in args.models]
    print_summary(results)

    args.out.write_text(json.dumps([asdict(r) for r in results], ensure_ascii=False, indent=2))
    print(f"\nResults written to {args.out}")


if __name__ == "__main__":
    main()
