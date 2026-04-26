"""Text normalization before classifier — UNIFIED_DESIGN §3.2 / Eunjin §6.4.

Two layers:
- `normalize`: cheap, safe — zero-width drop, NFKC, whitespace collapse, lowercase.
- `denoise`: aggressive — leetspeak reverse, spaced-out letter collapse.
  Caller should match against BOTH variants (don't destroy the original).
"""

from __future__ import annotations

import re
import unicodedata


_ZERO_WIDTH = re.compile(
    "["
    "᠎"          # Mongolian vowel separator
    "​-\u200F"   # ZWSP, ZWNJ, ZWJ, LRM, RLM
    "\u202A-\u202E"   # bidi overrides
    "⁠-⁤"   # word joiner, function application, ...
    "⁪-⁯"   # deprecated formatting
    "﻿"          # BOM / zero-width no-break space
    "]"
)
_WS_COLLAPSE = re.compile(r"\s+")

_LEET_MAP = str.maketrans({
    "0": "o",
    "1": "i",
    "3": "e",
    "4": "a",
    "5": "s",
    "7": "t",
    "@": "a",
    "$": "s",
})

_SPACED_RUN = re.compile(r"(?:\b[a-z]\b\s+){2,}\b[a-z]\b", re.IGNORECASE)


def normalize(text: str, *, drop_zero_width: bool = True, lowercase: bool = True) -> str:
    """Cheap, lossless-ish normalization. Safe to apply unconditionally."""
    if drop_zero_width:
        text = _ZERO_WIDTH.sub("", text)
    text = unicodedata.normalize("NFKC", text)
    text = _WS_COLLAPSE.sub(" ", text).strip()
    if lowercase:
        text = text.lower()
    return text


def denoise(text: str) -> str:
    """Aggressive obfuscation reversal. Lossy — use as a *parallel* variant for matching.

    Reverses:
    - leetspeak digit substitution (1gn0re → ignore)
    - spaced-out letter sequences ("i g n o r e" → "ignore"), runs of 3+ single chars only
    """
    text = text.translate(_LEET_MAP)
    text = _SPACED_RUN.sub(lambda m: m.group(0).replace(" ", ""), text)
    return text


def variants(text: str) -> list[str]:
    """Return matching variants of `text`, most-faithful first.

    1. `normalize(text)` — cheap pass.
    2. `denoise(...)` — leetspeak / spaced-letter reversal (only if it changes anything).
    3. all-whitespace-stripped form — defeats zero-width / space-sprinkle splits
       that break across word boundaries (e.g. `i g n o r e p r e v i o u s`).
    """
    norm = normalize(text)
    dn = denoise(norm)
    no_ws = re.sub(r"\s+", "", dn)
    out = [norm]
    if dn != norm:
        out.append(dn)
    if no_ws and no_ws not in out:
        out.append(no_ws)
    return out
