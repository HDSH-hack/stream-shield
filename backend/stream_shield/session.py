"""Shield session state."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ShieldSession:
    session_id: str
    upstream: Any  # Gemini WS connection
    policy: Any
    text_buffer: str = ""           # already-released-to-Gemini context
    pending_text: str = ""          # held back, not yet released
    transcript_buffer: str = ""     # auto-VAD transcript accumulation
    last_safe_offset: int = 0
    blocked: bool = False
    scores: list[float] = field(default_factory=list)
    receipts: list[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
