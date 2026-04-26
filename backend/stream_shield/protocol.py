"""Gemini Live API message parsing utilities.

Parses server→client messages (setupComplete, inputTranscription,
modelTurn, turnComplete, interrupted) and builds client→server
messages (setup, realtimeInput, clientContent).

Reference: UNIFIED_DESIGN.md Appendix + Gemini Live API docs.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


# ---------------------------------------------------------------------------
# Server → Client message types
# ---------------------------------------------------------------------------

class ServerEventType(str, Enum):
    SETUP_COMPLETE = "setupComplete"
    INPUT_TRANSCRIPTION = "inputTranscription"
    MODEL_TURN = "modelTurn"
    TURN_COMPLETE = "turnComplete"
    INTERRUPTED = "interrupted"
    UNKNOWN = "unknown"


@dataclass
class ServerEvent:
    type: ServerEventType
    text: str | None = None
    audio_data: bytes | None = None
    raw: dict[str, Any] | None = None


def parse_server_message(msg: dict[str, Any]) -> ServerEvent:
    """Parse a Gemini Live server message into a typed ServerEvent."""

    if "setupComplete" in msg:
        return ServerEvent(type=ServerEventType.SETUP_COMPLETE, raw=msg)

    sc = msg.get("serverContent", {})

    if "inputTranscription" in sc:
        text = sc["inputTranscription"].get("text", "")
        return ServerEvent(
            type=ServerEventType.INPUT_TRANSCRIPTION, text=text, raw=msg,
        )

    if "modelTurn" in sc:
        parts = sc["modelTurn"].get("parts", [])
        text_parts = [p["text"] for p in parts if "text" in p]
        text = "".join(text_parts) if text_parts else None
        audio = None
        for p in parts:
            if "inlineData" in p:
                import base64
                audio = base64.b64decode(p["inlineData"].get("data", ""))
                break
        return ServerEvent(
            type=ServerEventType.MODEL_TURN,
            text=text,
            audio_data=audio,
            raw=msg,
        )

    if sc.get("turnComplete"):
        return ServerEvent(type=ServerEventType.TURN_COMPLETE, raw=msg)

    if sc.get("interrupted"):
        return ServerEvent(type=ServerEventType.INTERRUPTED, raw=msg)

    return ServerEvent(type=ServerEventType.UNKNOWN, raw=msg)


# ---------------------------------------------------------------------------
# Client → Server message builders
# ---------------------------------------------------------------------------

def build_setup_message(
    model: str = "models/gemini-3.1-flash-live-preview",
    *,
    response_modalities: list[str] | None = None,
    system_instruction: str | None = None,
) -> dict[str, Any]:
    """Build the initial setup message for Gemini Live session."""
    if response_modalities is None:
        response_modalities = ["TEXT"]

    setup: dict[str, Any] = {
        "model": model,
        "generation_config": {
            "response_modalities": response_modalities,
            "input_audio_transcription": {},
        },
        "realtime_input_config": {
            "automatic_activity_detection": {
                "disabled": False,
                "start_of_speech_sensitivity": "START_SENSITIVITY_HIGH",
                "end_of_speech_sensitivity": "END_SENSITIVITY_HIGH",
            },
        },
    }

    if system_instruction:
        setup["system_instruction"] = {
            "parts": [{"text": system_instruction}],
        }

    return {"setup": setup}


def build_audio_input(audio_b64: str, mime: str = "audio/pcm;rate=16000") -> dict[str, Any]:
    """Build a realtimeInput message with audio data."""
    return {
        "realtimeInput": {
            "mediaChunks": [{"mimeType": mime, "data": audio_b64}],
        },
    }


def build_text_input(text: str) -> dict[str, Any]:
    """Build a clientContent message with text (for hold→scan→release path)."""
    return {
        "clientContent": {
            "turns": [{"role": "user", "parts": [{"text": text}]}],
            "turnComplete": True,
        },
    }


def build_activity_signals(start: bool = True) -> dict[str, Any]:
    """Build activityStart / activityEnd for push-to-talk fallback."""
    key = "activityStart" if start else "activityEnd"
    return {"realtimeInput": {key: {}}}
