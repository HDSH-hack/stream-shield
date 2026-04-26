"""L0 rules pass — UNIFIED_DESIGN §3.2.

Cheap regex / role-spoof / external-destination match on normalized text.
Target latency: <1ms per scan. Hard rules only — score is 1.0 on match, 0.0 otherwise.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from stream_shield.guard.decision import Verdict
from stream_shield.guard.normalizer import variants
from stream_shield.policy import Policy


@dataclass
class CompiledRules:
    block_phrases: list[re.Pattern[str]]
    block_phrases_nospace: list[re.Pattern[str]]
    role_spoof: list[re.Pattern[str]]
    external_dest: list[re.Pattern[str]]


_WS = re.compile(r"\s+")


def compile_rules(policy: Policy) -> CompiledRules:
    flags = re.IGNORECASE | re.DOTALL
    return CompiledRules(
        block_phrases=[re.compile(p, flags) for p in policy.block_phrases],
        block_phrases_nospace=[re.compile(_WS.sub("", p), flags) for p in policy.block_phrases],
        role_spoof=[re.compile(p, flags) for p in policy.role_spoof_regex],
        external_dest=[re.compile(re.escape(p), flags) for p in policy.block_external_dest],
    )


def scan(text: str, rules: CompiledRules) -> Verdict:
    """Return Verdict(layer="L0"). Empty text → safe.

    Matches against both the cheap-normalized text and the aggressively-denoised
    variant (leetspeak / spaced-out letters reversed) — see normalizer.variants.
    """
    if not text:
        return Verdict(score=0.0, label="safe", layer="L0")

    cands = variants(text)

    for candidate in cands:
        for pat in rules.role_spoof:
            m = pat.search(candidate)
            if m:
                return _hit("role_spoof", pat, m, candidate)
        for pat in rules.block_phrases:
            m = pat.search(candidate)
            if m:
                return _hit("block_phrase", pat, m, candidate)
        for pat in rules.external_dest:
            m = pat.search(candidate)
            if m:
                return _hit("external_dest", pat, m, candidate)

    no_ws = _WS.sub("", cands[-1])
    for pat in rules.block_phrases_nospace:
        m = pat.search(no_ws)
        if m:
            return _hit("block_phrase_nospace", pat, m, no_ws)

    return Verdict(score=0.0, label="safe", layer="L0")


def _hit(kind: str, pat: re.Pattern[str], m: re.Match[str], variant: str) -> Verdict:
    return Verdict(
        score=1.0,
        label="malicious",
        layer="L0",
        reason=f"{kind} match: {pat.pattern!r}",
        extra={"matched": m.group(0), "kind": kind, "variant": variant},
    )
