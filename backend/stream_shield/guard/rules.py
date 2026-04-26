"""L0 rules pass — UNIFIED_DESIGN §3.2.

Cheap regex / role-spoof / external-destination match on normalized text.
Target latency: <1ms per scan. Hard rules only — score is 1.0 on match,
0.0 otherwise.

Optimizations vs naive impl:
  - Per-category patterns are joined into ONE alternation (`(?:p1)|(?:p2)|...`).
    Each variant is searched once per category instead of once per pattern,
    cutting the inner loop from O(V*P) to O(V*C) where C = 4 categories.
  - Compiled rule sets are cached by policy signature so concurrent sessions
    on the same policy share the work.
  - Per-pattern attribution is preserved for the BLOCK reason via a separate
    fallback search across the original pattern list — only run on a hit
    (rare path).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from threading import Lock

from stream_shield.guard.decision import Verdict
from stream_shield.guard.normalizer import variants
from stream_shield.policy import Policy


@dataclass
class CompiledRules:
    # Joined alternation per category (None when policy has 0 patterns).
    block_phrases: re.Pattern[str] | None
    block_phrases_nospace: re.Pattern[str] | None
    role_spoof: re.Pattern[str] | None
    external_dest: re.Pattern[str] | None
    # Original pattern strings retained for hit attribution.
    raw_block_phrases: tuple[str, ...] = field(default_factory=tuple)
    raw_role_spoof: tuple[str, ...] = field(default_factory=tuple)
    raw_external_dest: tuple[str, ...] = field(default_factory=tuple)


_WS = re.compile(r"\s+")
_FLAGS = re.IGNORECASE | re.DOTALL

_RULES_CACHE: dict[tuple, CompiledRules] = {}
_RULES_CACHE_LOCK = Lock()


def _join(patterns: list[str], *, escape: bool = False) -> re.Pattern[str] | None:
    """Combine N patterns into one alternation. Skips invalid regex by escaping."""
    if not patterns:
        return None
    parts: list[str] = []
    for p in patterns:
        if escape:
            parts.append(re.escape(p))
        else:
            try:
                re.compile(p)  # validate; if it throws we'll escape
                parts.append(f"(?:{p})")
            except re.error:
                parts.append(re.escape(p))
    return re.compile("|".join(parts), _FLAGS)


def compile_rules(policy: Policy) -> CompiledRules:
    """Compile + cache rule patterns for a policy. Thread-safe."""
    key = (
        policy.policy_id,
        tuple(policy.block_phrases),
        tuple(policy.role_spoof_regex),
        tuple(policy.block_external_dest),
    )
    cached = _RULES_CACHE.get(key)
    if cached is not None:
        return cached

    with _RULES_CACHE_LOCK:
        cached = _RULES_CACHE.get(key)  # double-check
        if cached is not None:
            return cached

        compiled = CompiledRules(
            block_phrases=_join(policy.block_phrases),
            block_phrases_nospace=_join([_WS.sub("", p) for p in policy.block_phrases]),
            role_spoof=_join(policy.role_spoof_regex),
            external_dest=_join(policy.block_external_dest, escape=True),
            raw_block_phrases=tuple(policy.block_phrases),
            raw_role_spoof=tuple(policy.role_spoof_regex),
            raw_external_dest=tuple(policy.block_external_dest),
        )
        _RULES_CACHE[key] = compiled
        return compiled


def _attribute(matched: str, raw_patterns: tuple[str, ...], escape: bool = False) -> str:
    """Find which raw pattern produced the match — for the BLOCK reason."""
    for p in raw_patterns:
        try:
            pat = re.compile(re.escape(p) if escape else p, _FLAGS)
        except re.error:
            pat = re.compile(re.escape(p), _FLAGS)
        if pat.search(matched):
            return p
    return raw_patterns[0] if raw_patterns else "?"


def scan(text: str, rules: CompiledRules) -> Verdict:
    """Return Verdict(layer="L0"). Empty text → safe.

    Tests every variant (NFKC / leetspeak-reversed / etc.) once per category.
    """
    if not text:
        return Verdict(score=0.0, label="safe", layer="L0")

    cands = variants(text)

    for candidate in cands:
        if rules.role_spoof and (m := rules.role_spoof.search(candidate)):
            pat_str = _attribute(m.group(0), rules.raw_role_spoof)
            return _hit("role_spoof", pat_str, m, candidate)
        if rules.block_phrases and (m := rules.block_phrases.search(candidate)):
            pat_str = _attribute(m.group(0), rules.raw_block_phrases)
            return _hit("block_phrase", pat_str, m, candidate)
        if rules.external_dest and (m := rules.external_dest.search(candidate)):
            pat_str = _attribute(m.group(0), rules.raw_external_dest, escape=True)
            return _hit("external_dest", pat_str, m, candidate)

    if rules.block_phrases_nospace:
        no_ws = _WS.sub("", cands[-1])
        if m := rules.block_phrases_nospace.search(no_ws):
            pat_str = _attribute(m.group(0), rules.raw_block_phrases)
            return _hit("block_phrase_nospace", pat_str, m, no_ws)

    return Verdict(score=0.0, label="safe", layer="L0")


def _hit(kind: str, pattern: str, m: re.Match[str], variant: str) -> Verdict:
    return Verdict(
        score=1.0,
        label="malicious",
        layer="L0",
        reason=f"{kind} match: {pattern!r}",
        extra={"matched": m.group(0), "kind": kind, "variant": variant},
    )
