"""Gemini Live API PoC — auto VAD + inputTranscription timing test.

Phase 0 goal: verify that inputTranscription arrives before or
concurrently with modelTurn, so we can run the classifier in
parallel with response generation.

Usage:
    export GEMINI_API_KEY=...
    cd backend
    source .venv/bin/activate
    python notebooks/gemini_live_poc.py
"""

from __future__ import annotations

import asyncio
import io
import logging
import os
import subprocess
import tempfile
import time

import av
from google import genai
from google.genai import types

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s.%(msecs)03d %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("poc")

MODEL = "models/gemini-3.1-flash-live-preview"
RECV_TIMEOUT = 15  # seconds


# ---------------------------------------------------------------------------
# Audio helpers
# ---------------------------------------------------------------------------

def tts_to_pcm(text: str, lang: str = "en") -> bytes:
    """Use macOS `say` to synthesize speech, convert to PCM s16le 16kHz mono via av."""
    voice = "Yuna" if lang == "ko" else "Samantha"
    with tempfile.NamedTemporaryFile(suffix=".aiff", delete=True) as tmp:
        subprocess.run(
            ["say", "-v", voice, "-o", tmp.name, text],
            check=True, capture_output=True,
        )
        return aiff_to_pcm(tmp.name)


def aiff_to_pcm(path: str, target_rate: int = 16000) -> bytes:
    """Convert audio file to PCM s16le mono at target_rate using av."""
    output = io.BytesIO()
    container = av.open(path)
    resampler = av.AudioResampler(
        format="s16", layout="mono", rate=target_rate,
    )
    for frame in container.decode(audio=0):
        for resampled in resampler.resample(frame):
            output.write(resampled.planes[0])
    container.close()
    return output.getvalue()


# ---------------------------------------------------------------------------
# Event collector with timeout
# ---------------------------------------------------------------------------

async def collect_events(session, label: str, t0: float, timeout: float = RECV_TIMEOUT) -> list[dict]:
    """Receive server events until turnComplete/interrupted or timeout."""
    events = []

    async def _recv():
        async for msg in session.receive():
            elapsed_ms = (time.monotonic() - t0) * 1000
            sc = msg.server_content
            if sc is None:
                continue

            if sc.input_transcription:
                events.append({
                    "type": "inputTranscription",
                    "elapsed_ms": round(elapsed_ms, 1),
                    "text": sc.input_transcription.text or "",
                })
                logger.info("[%s] +%6.1fms inputTranscription: %r",
                            label, elapsed_ms, sc.input_transcription.text)

            if sc.model_turn:
                parts = sc.model_turn.parts or []
                text_parts = [p.text for p in parts if p.text]
                has_audio = any(p.inline_data for p in parts if hasattr(p, "inline_data") and p.inline_data)
                desc = "".join(text_parts)[:80] if text_parts else ("(audio)" if has_audio else "(empty)")
                events.append({
                    "type": "modelTurn",
                    "elapsed_ms": round(elapsed_ms, 1),
                    "text": desc,
                })
                logger.info("[%s] +%6.1fms modelTurn: %s", label, elapsed_ms, desc)

            if sc.turn_complete:
                events.append({"type": "turnComplete", "elapsed_ms": round(elapsed_ms, 1)})
                logger.info("[%s] +%6.1fms turnComplete", label, elapsed_ms)
                return

            if sc.interrupted:
                events.append({"type": "interrupted", "elapsed_ms": round(elapsed_ms, 1)})
                logger.info("[%s] +%6.1fms interrupted", label, elapsed_ms)
                return

    try:
        await asyncio.wait_for(_recv(), timeout=timeout)
    except asyncio.TimeoutError:
        events.append({"type": "TIMEOUT", "elapsed_ms": round((time.monotonic() - t0) * 1000, 1)})
        logger.warning("[%s] Timeout after %.0fs", label, timeout)

    return events


# ---------------------------------------------------------------------------
# Test turn: send audio via realtimeInput
# ---------------------------------------------------------------------------

async def run_audio_turn(session, text: str, lang: str, label: str) -> dict:
    """Synthesize speech from text, send as audio realtimeInput, measure timing."""
    logger.info("[%s] Synthesizing TTS: %r (lang=%s)", label, text, lang)
    pcm = tts_to_pcm(text, lang=lang)
    logger.info("[%s] PCM ready: %d bytes (%.1fs at 16kHz)", label, len(pcm), len(pcm) / 2 / 16000)

    t0 = time.monotonic()

    # Send audio in ~100ms chunks (3200 bytes = 100ms at 16kHz s16le mono)
    chunk_size = 3200
    silence_chunk = b"\x00" * chunk_size

    for i in range(0, len(pcm), chunk_size):
        chunk = pcm[i : i + chunk_size]
        await session.send_realtime_input(
            audio=types.Blob(mime_type="audio/pcm;rate=16000", data=chunk),
        )
        await asyncio.sleep(0.1)  # real-time pacing

    # Send 2s of silence so auto-VAD detects end of speech
    for _ in range(20):
        await session.send_realtime_input(
            audio=types.Blob(mime_type="audio/pcm;rate=16000", data=silence_chunk),
        )
        await asyncio.sleep(0.1)

    send_done_ms = (time.monotonic() - t0) * 1000
    logger.info("[%s] Audio + silence sent (+%.0fms), waiting for VAD + response...", label, send_done_ms)

    events = await collect_events(session, label, t0)

    return {"label": label, "input_text": text, "lang": lang, "pcm_bytes": len(pcm), "events": events}


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def main():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        logger.error("Set GEMINI_API_KEY environment variable")
        return

    client = genai.Client(api_key=api_key)

    config = types.LiveConnectConfig(
        response_modalities=["AUDIO"],
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

    logger.info("Connecting to %s ...", MODEL)
    async with client.aio.live.connect(model=MODEL, config=config) as session:
        logger.info("Session established")

        # Test 1: English
        r1 = await run_audio_turn(session, "Hello, what is two plus two?", lang="en", label="audio-en")
        results.append(r1)

        await asyncio.sleep(2)  # let session settle

        # Test 2: Korean
        r2 = await run_audio_turn(session, "내일 오후 3시 미팅 잡아줘", lang="ko", label="audio-ko")
        results.append(r2)

    # --- Summary ---
    print("\n" + "=" * 70)
    print("PHASE 0 PoC RESULTS — Gemini Live inputTranscription Timing")
    print(f"Model: {MODEL}")
    print("=" * 70)

    for r in results:
        print(f"\n[{r['label']}]  input: {r['input_text']}  ({r['pcm_bytes']} bytes PCM)")

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
                print(f"  >> transcript {abs(delta):.0f}ms BEFORE modelTurn -> parallel pipeline viable")
            else:
                print(f"  >> transcript {delta:.0f}ms AFTER modelTurn -> response buffer needed ({delta:.0f}ms)")
        elif transcript_ms is None:
            print("  >> NO inputTranscription received")
        elif first_model_ms is None:
            print("  >> NO modelTurn received")

    print("\n" + "=" * 70)
    print("KEY QUESTION: does inputTranscription arrive before first modelTurn?")
    print("  YES -> parallel pipeline (audio forwarded, classify on transcript)")
    print("  NO  -> response buffer delay needed (buffer modelTurn chunks)")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
