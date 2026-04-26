"""Decision types — UNIFIED_DESIGN §2.2 D4."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Action(str, Enum):
    ALLOW = "ALLOW"
    HOLD = "HOLD"
    BLOCK = "BLOCK"
    AUGMENT = "AUGMENT"          # stretch
    QUARANTINE = "QUARANTINE"    # stretch


@dataclass
class Verdict:
    score: float
    label: str = "safe"          # safe | suspicious | malicious
    layer: str = ""              # L0 | L1 | L2
    reason: str = ""
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class Decision:
    action: Action
    verdict: Verdict | None = None
    forward: dict[str, Any] | None = None  # message to send upstream
    reason: str = ""
    score: float = 0.0
