"""Per-entity policy YAML loader."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


CONFIG_DIR = Path(__file__).parent.parent / "config"


@dataclass
class Thresholds:
    safe: float = 0.35
    block: float = 0.70
    judge_band: tuple[float, float] = (0.35, 0.70)


@dataclass
class BufferConfig:
    min_chars: int = 48
    overlap_chars: int = 128
    scan_interval_ms: int = 150
    response_buffer_ms: int = 100


@dataclass
class GuardConfig:
    primary_model: str = "meta-llama/Llama-Prompt-Guard-2-86M"
    runtime: str = "transformers"
    max_length: int = 512
    l2_judge_enabled: bool = False
    l2_judge_model: str = "google/gemma-2-2b-it"


@dataclass
class Policy:
    policy_id: str = "default"
    language: list[str] = field(default_factory=lambda: ["ko", "en"])
    thresholds: Thresholds = field(default_factory=Thresholds)
    buffer: BufferConfig = field(default_factory=BufferConfig)
    guard: GuardConfig = field(default_factory=GuardConfig)
    block_phrases: list[str] = field(default_factory=list)
    role_spoof_regex: list[str] = field(default_factory=list)
    block_external_dest: list[str] = field(default_factory=list)
    pii_categories: list[str] = field(default_factory=list)
    receipt_enabled: bool = False


def load_policy(policy_id: str = "default") -> Policy:
    path = CONFIG_DIR / f"policy.{policy_id}.yaml"
    if not path.exists():
        path = CONFIG_DIR / "policy.default.yaml"
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))

    # Merge with parent if `extends` set: load parent raw YAML, then child overrides per top-level key.
    if "extends" in raw:
        parent_path = CONFIG_DIR / f"policy.{raw['extends']}.yaml"
        if parent_path.exists():
            parent_raw = yaml.safe_load(parent_path.read_text(encoding="utf-8")) or {}
            merged: dict[str, Any] = {}
            for k, v in parent_raw.items():
                merged[k] = v
            for k, v in raw.items():
                if k == "extends":
                    continue
                if isinstance(v, dict) and isinstance(merged.get(k), dict):
                    nested = dict(merged[k])
                    nested.update(v)
                    merged[k] = nested
                else:
                    merged[k] = v
            raw = merged

    p = Policy(policy_id=raw.get("policy_id", policy_id))
    if "thresholds" in raw:
        t = raw["thresholds"]
        p.thresholds = Thresholds(
            safe=t.get("safe", 0.35),
            block=t.get("block", 0.70),
            judge_band=tuple(t.get("judge_band", [0.35, 0.70])),
        )
    if "buffer" in raw:
        b = raw["buffer"]
        p.buffer = BufferConfig(
            min_chars=b.get("min_chars", 48),
            overlap_chars=b.get("overlap_chars", 128),
            scan_interval_ms=b.get("scan_interval_ms", 150),
            response_buffer_ms=b.get("response_buffer_ms", 100),
        )
    if "guard" in raw:
        g = raw["guard"]
        p.guard = GuardConfig(
            primary_model=g.get("primary_model", GuardConfig.primary_model),
            runtime=g.get("runtime", "transformers"),
            max_length=g.get("max_length", 512),
            l2_judge_enabled=g.get("l2_judge", {}).get("enabled", False),
            l2_judge_model=g.get("l2_judge", {}).get("model", GuardConfig.l2_judge_model),
        )
    rules = raw.get("rules", {})
    p.block_phrases = rules.get("block_phrases", [])
    p.role_spoof_regex = rules.get("role_spoof_regex", [])
    domain = raw.get("domain", {})
    p.block_external_dest = domain.get("block_external_dest", [])
    p.pii_categories = domain.get("pii_categories", [])
    p.receipt_enabled = raw.get("receipt", {}).get("enabled", False)
    return p
