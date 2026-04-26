"""Gemini Live API PoC — auto VAD + inputTranscription timing test.

Phase 0 goal: verify that inputTranscription arrives before or
concurrently with modelTurn, so we can run the classifier in
parallel with response generation.

Usage:
    export GEMINI_API_KEY=...
    cd backend
    source .venv/bin/activate
    python notebooks/gemini_live_poc.py

The script sends a short pre-recorded audio clip (or synthesized
PCM silence + text fallback) and logs the exact arrival order and
timestamps of server events.
"""

from __future__ import annotations

import asyncio
import base64
import logging
import os
import struct
import time

from google import genai
from google.genai import types

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s.%(msecs)03d %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("poc")

MODEL = "models/gemini-2.0-flash-live-001"


def generate_pcm_silence(duration_s: float = 0.5, sample_rate: int = 16000) -> bytes:
    """Generate silent PCM s16le audio for testing."""
    num_samples = int(duration_s * sample_rate)
    return struct.pack(f"<{num_samples}h", *([0] * num_samples))


def generate_pcm_tone(duration_s: float = 0.3, freq: float = 440.0, sample_rate: int = 16000) -> bytes:
    """Generate a simple sine tone as PCM s16le for testing."""
    import math
    num_samples = int(duration_s * sample_rate)
    samples = []
    for i in range(num_samples):
        t = i / sample_rate
        val = int(16000 * math.sin(2 * math.pi * freq * t))
        samples.append(max(-32768, min(32767, val)))
    return struct.pack(f"<{num_samples}h", *samples)


async def run_text_turn(session, text: str, label: str) -> dict:
    """Send a text turn via clientContent and measure event timing."""
    events = []
    t0 = time.monotonic()

    logger.info("[%s] Sending text: %r", label, text)

    await session.send_client_content(
        turns=[types.Content(role="user", parts=[types.Part(text=text)])],
        turn_complete=True,
    )

    async for msg in session.receive():
        elapsed_ms = (time.monotonic() - t0) * 1000
        sc = msg.server_content

        if sc is None:
            continue

        if sc.input_transcription:
            events.append({
                "type": "inputTranscription",
                "elapsed_ms": round(elapsed_ms, 1),
                "text": sc.input_transcription.text,
            })
            logger.info(
                "[%s] +%6.1fms inputTranscription: %r",
                label, elapsed_ms, sc.input_transcription.text,
            )

        if sc.model_turn:
            parts = sc.model_turn.parts or []
            text_parts = [p.text for p in parts if p.text]
            events.append({
                "type": "modelTurn",
                "elapsed_ms": round(elapsed_ms, 1),
                "text": "".join(text_parts) if text_parts else "(audio/empty)",
            })
            logger.info(
                "[%s] +%6.1fms modelTurn: %s",
                label, elapsed_ms, "".join(text_parts)[:80] if text_parts else "(non-text)",
            )

        if sc.turn_complete:
            events.append({
                "type": "turnComplete",
                "elapsed_ms": round(elapsed_ms, 1),
            })
            logger.info("[%s] +%6.1fms turnComplete", label, elapsed_ms)
            break

        if sc.interrupted:
            events.append({
                "type": "interrupted",
                "elapsed_ms": round(elapsed_ms, 1),
            })
            logger.info("[%s] +%6.1fms interrupted", label, elapsed_ms)
            break

    return {"label": label, "input": text, "events": events}


async def run_audio_turn(session, audio_pcm: bytes, label: str) -> dict:
    """Send audio via realtimeInput and measure event timing."""
    events = []
    t0 = time.monotonic()

    chunk_size = 4800  # 150ms at 16kHz mono s16le (2 bytes/sample)
    logger.info("[%s] Sending %d bytes of audio in %d-byte chunks",
                label, len(audio_pcm), chunk_size)

    # Send audio in chunks
    for i in range(0, len(audio_pcm), chunk_size):
        chunk = audio_pcm[i : i + chunk_size]
        b64 = base64.b64encode(chunk).decode()
        await session.send_realtime_input(
            media_chunks=[
                types.Blob(mime_type="audio/pcm;rate=16000", data=chunk),
            ],
        )
        await asyncio.sleep(0.15)  # simulate real-time pacing

    # Signal end of audio activity
    logger.info("[%s] Audio sent, waiting for events...", label)

    # Collect events with timeout
    try:
        async for msg in session.receive():
            elapsed_ms = (time.monotonic() - t0) * 1000
            sc = msg.server_content

            if sc is None:
                continue

            if sc.input_transcription:
                events.append({
                    "type": "inputTranscription",
                    "elapsed_ms": round(elapsed_ms, 1),
                    "text": sc.input_transcription.text,
                })
                logger.info(
                    "[%s] +%6.1fms inputTranscription: %r",
                    label, elapsed_ms, sc.input_transcription.text,
                )

            if sc.model_turn:
                parts = sc.model_turn.parts or []
                text_parts = [p.text for p in parts if p.text]
                events.append({
                    "type": "modelTurn",
                    "elapsed_ms": round(elapsed_ms, 1),
                    "text": "".join(text_parts) if text_parts else "(audio/empty)",
                })
                logger.info(
                    "[%s] +%6.1fms modelTurn: %s",
                    label, elapsed_ms, "".join(text_parts)[:80] if text_parts else "(non-text)",
                )

            if sc.turn_complete:
                events.append({
                    "type": "turnComplete",
                    "elapsed_ms": round(elapsed_ms, 1),
                })
                logger.info("[%s] +%6.1fms turnComplete", label, elapsed_ms)
                break

            if sc.interrupted:
                events.append({
                    "type": "interrupted",
                    "elapsed_ms": round(elapsed_ms, 1),
                })
                logger.info("[%s] +%6.1fms interrupted", label, elapsed_ms)
                break

    except asyncio.TimeoutError:
        logger.warning("[%s] Timeout waiting for events", label)

    return {"label": label, "events": events}


async def main():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        logger.error("Set GEMINI_API_KEY environment variable")
        return

    client = genai.Client(api_key=api_key)

    config = types.LiveConnectConfig(
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

    results = []

    async with client.aio.live.connect(model=MODEL, config=config) as session:
        logger.info("Session established")

        # --- Test 1: text turn (clientContent) ---
        r1 = await run_text_turn(session, "Hello, what is 2+2?", label="text-en")
        results.append(r1)

        await asyncio.sleep(1)

        # --- Test 2: Korean text turn ---
        r2 = await run_text_turn(session, "내일 오후 3시 미팅 잡아줘", label="text-ko")
        results.append(r2)

    # --- Summary ---
    print("\n" + "=" * 60)
    print("PHASE 0 PoC RESULTS — Gemini Live Timing")
    print("=" * 60)

    for r in results:
        print(f"\n[{r['label']}]")
        if "input" in r:
            print(f"  Input: {r['input']}")

        transcript_ms = None
        first_model_ms = None

        for ev in r["events"]:
            tag = ev["type"]
            ms = ev["elapsed_ms"]
            extra = ev.get("text", "")
            print(f"  +{ms:7.1f}ms  {tag:25s}  {extra[:60]}")

            if tag == "inputTranscription" and transcript_ms is None:
                transcript_ms = ms
            if tag == "modelTurn" and first_model_ms is None:
                first_model_ms = ms

        if transcript_ms is not None and first_model_ms is not None:
            delta = transcript_ms - first_model_ms
            if delta <= 0:
                print(f"  >> transcript arrived {abs(delta):.1f}ms BEFORE first modelTurn -> parallel OK")
            else:
                print(f"  >> transcript arrived {delta:.1f}ms AFTER first modelTurn -> need response buffer")

    print("\n" + "=" * 60)
    print("Decision: check if inputTranscription arrives before modelTurn.")
    print("  YES -> parallel pipeline (Gihwang) viable")
    print("  NO  -> hold-and-scan (Eunjin) or response buffer needed")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
