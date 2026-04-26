"""Text normalization before classifier — UNIFIED_DESIGN §3.2 / Eunjin §6.4."""

from __future__ import annotations

import re
import unicodedata


_ZERO_WIDTH = re.compile(r"[​-‏‪-‮﻿]")
_WS_COLLAPSE = re.compile(r"\s+")


def normalize(text: str, *, drop_zero_width: bool = True, lowercase: bool = True) -> str:
    if drop_zero_width:
        text = _ZERO_WIDTH.sub("", text)
    text = unicodedata.normalize("NFKC", text)
    text = _WS_COLLAPSE.sub(" ", text).strip()
    if lowercase:
        text = text.lower()
    return text
