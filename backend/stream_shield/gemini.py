"""Gemini Live API async client wrapper.

Uses google-genai SDK's async Live session with auto-VAD and
inputTranscription enabled.  Returns an AsyncSession that the
proxy server relays through.

See UNIFIED_DESIGN.md §2.2 D1 for design rationale.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator

from google import genai
from google.genai import types

from stream_shield.policy import Policy

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "models/gemini-2.0-flash-live-001"


def _build_live_config(policy: Policy) -> types.LiveConnectConfig:
    """Build LiveConnectConfig from our Policy dataclass."""
    return types.LiveConnectConfig(
        response_modalities=["TEXT"],
        input_audio_transcription=types.AudioTranscriptionConfig(),
        realtime_input_config=types.RealtimeInputConfig(
            automatic_activity_detection=types.AutomaticActivityDetection(
                disabled=False,
                start_of_speech_sensitivity=types.StartSensitivity.START_SENSITIVITY_HIGH,
                end_of_speech_sensitivity=types.EndSensitivity.END_SENSITIVITY_HIGH,
            ),
        ),
    )


@asynccontextmanager
async def connect_gemini(
    *,
    api_key: str,
    policy: Policy,
    model: str = DEFAULT_MODEL,
) -> AsyncIterator[Any]:
    """Open a Gemini Live session with auto-VAD + transcription.

    Usage::

        async with connect_gemini(api_key=key, policy=policy) as session:
            await session.send_realtime_input(...)
            async for msg in session:
                ...
    """
    client = genai.Client(api_key=api_key)
    config = _build_live_config(policy)

    logger.info("connecting to Gemini Live: model=%s", model)
    async with client.aio.live.connect(model=model, config=config) as session:
        logger.info("Gemini Live session established")
        yield session
