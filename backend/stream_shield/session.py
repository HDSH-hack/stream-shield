"""Shield session state."""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class SessionState(str, Enum):
    RELAYING = "RELAYING"      # audio relay, no classification pending
    JUDGING = "JUDGING"        # classifier running, modelTurn buffered
    SAFE = "SAFE"              # classifier passed, flushing buffer
    BLOCKED = "BLOCKED"        # classifier blocked, dropping buffer


@dataclass
class ShieldSession:
    session_id: str
    upstream: Any                          # Gemini Live AsyncSession
    policy: Any
    state: SessionState = SessionState.RELAYING

    # Transcript accumulation (from Gemini inputTranscription)
    transcript_buffer: str = ""            # accumulated transcript for current turn

    # Classifier
    pending_verdict: asyncio.Task | None = None  # running classify task

    # Stats
    total_turns: int = 0
    blocked_turns: int = 0
    scores: list[float] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)

    def reset_turn(self) -> None:
        """Reset per-turn state for next utterance."""
        self.transcript_buffer = ""
        self.pending_verdict = None
        self.state = SessionState.RELAYING
