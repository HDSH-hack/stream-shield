"""FastAPI WebSocket server — Stream Shield entry point.

Architecture (single-response, parallel-classify pipeline):
1. Client audio (JSON base64) → Proxy → Gemini (auto-VAD, STT)
2. input_transcription side-channel → start classifier in background
3. Gemini's auto-response chunks (model_turn audio + output_transcription text)
   are *buffered* in the proxy while the classifier runs
4. On turn_complete:
     SAFE  → flush buffered text + audio to client + final marker
     BLOCK → drop buffered chunks + send 'blocked' event

One Gemini generation per turn — no clientContent re-issue.

Frontend interface: see docs/api.md
"""

from __future__ import annotations

import asyncio
import base64
import json
import logging
import os
from pathlib import Path
from typing import Annotated

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Path
from fastapi.middleware.cors import CORSMiddleware
from google.genai import types
from starlette.websockets import WebSocketState

from stream_shield.gemini import connect_gemini
from stream_shield.guard.engine import GuardEngine
from stream_shield.guard.decision import Action
from stream_shield.buffer.manager import BufferManager
from stream_shield.policy import load_policy
from stream_shield.session import ShieldSession, SessionState

logger = logging.getLogger(__name__)

app = FastAPI(title="Stream Shield", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}


@app.websocket("/ws/{session_id}")
async def shield_ws(
    ws: WebSocket,
    session_id: Annotated[str, Path(min_length=1, max_length=64)],
):
    await ws.accept()
    policy_id = ws.query_params.get("policy", "default")
    policy = load_policy(policy_id)

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        await ws.send_json({"type": "error", "message": "GEMINI_API_KEY not set"})
        await ws.close()
        return

    guard = GuardEngine(policy=policy)
    await guard.warmup()
    buffer_mgr = BufferManager(guard=guard, policy=policy)

    try:
        async with connect_gemini(api_key=api_key, policy=policy) as gemini:
            session = ShieldSession(
                session_id=session_id,
                upstream=gemini,
                policy=policy,
            )
            logger.info("session %s started (policy=%s)", session_id, policy_id)
            await ws.send_json({
                "type": "session_started",
                "session_id": session_id,
                "policy_id": policy_id,
            })
            client_task = asyncio.create_task(_handle_client(ws, session, buffer_mgr))
            gemini_task = asyncio.create_task(_handle_gemini(ws, session, buffer_mgr))
            done, pending = await asyncio.wait(
                {client_task, gemini_task},
                return_when=asyncio.FIRST_COMPLETED,
            )
            for task in pending:
                task.cancel()
            if pending:
                await asyncio.gather(*pending, return_exceptions=True)
            for task in done:
                task.result()
    except WebSocketDisconnect:
        logger.info("client disconnected: %s", session_id)
    except Exception as e:
        logger.exception("session error: %s", session_id)
        if ws.client_state == WebSocketState.CONNECTED:
            await ws.send_json({"type": "error", "message": str(e)})
            await ws.close()


# ---------------------------------------------------------------------------
# Client → Backend
# ---------------------------------------------------------------------------

async def _handle_client(ws, session: ShieldSession, buffer_mgr: BufferManager):
    """Handle frontend messages: realtimeInput.audio JSON frames."""
    while True:
        raw = await ws.receive()
        if raw.get("type") == "websocket.disconnect":
            break

        text = raw.get("text")
        if not text:
            continue

        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            continue

        msg_type = data.get("type", "")
        seq = data.get("seq", 0)
        session.last_client_seq = seq

        if msg_type == "realtimeInput.audio":
            # JSON base64 audio → decode → forward to Gemini
            b64 = data.get("data", "")
            if b64:
                pcm = base64.b64decode(b64)
                await session.upstream.send_realtime_input(
                    audio=types.Blob(
                        mime_type="audio/pcm;rate=16000",
                        data=pcm,
                    ),
                )



# ---------------------------------------------------------------------------
# Gemini → Client
# ---------------------------------------------------------------------------

async def _handle_gemini(ws, session: ShieldSession, buffer_mgr: BufferManager):
    """Handle Gemini Live events, apply guard, relay to frontend.

    Single-response, parallel-classify pipeline:
      input_transcription → start classifier (background)
      output_transcription → buffer text deltas
      model_turn audio chunks → buffer audio
      turn_complete → await verdict:
          BLOCK → drop buffers + send 'blocked'
          SAFE  → flush text deltas + audio bytes + final marker

    No clientContent re-issue. One Gemini generation per turn.
    """
    pending_text: list[str] = []
    pending_audio: list[bytes] = []

    def reset_buffers() -> None:
        pending_text.clear()
        pending_audio.clear()

    async for msg in session.upstream.receive():
        sc = msg.server_content
        if sc is None:
            continue

        # --- input transcription → start classifier (parallel) ---
        if sc.input_transcription and sc.input_transcription.text:
            transcript = sc.input_transcription.text
            logger.info("transcript: %r", transcript[:80])
            session.transcript_buffer = transcript
            session.state = SessionState.JUDGING
            reset_buffers()

            await ws.send_json({
                "type": "transcript",
                "seq": session.next_seq(),
                "text": transcript,
                "final": True,
            })

            session.pending_verdict = asyncio.create_task(
                buffer_mgr.classify(session, transcript)
            )

        # --- output transcription text deltas → buffer ---
        out_tx = getattr(sc, "output_transcription", None)
        if out_tx is not None:
            text = getattr(out_tx, "text", None) or ""
            if text and session.state in (SessionState.JUDGING, SessionState.RELAYING):
                pending_text.append(text)

        # --- model_turn (audio + occasional inline text) → buffer ---
        if sc.model_turn and session.state in (SessionState.JUDGING, SessionState.RELAYING):
            for part in sc.model_turn.parts or []:
                if part.text:
                    pending_text.append(part.text)
                if part.inline_data and part.inline_data.data:
                    pending_audio.append(part.inline_data.data)

        # --- turn_complete → resolve verdict, flush or drop ---
        if sc.turn_complete:
            decision = None
            if session.pending_verdict:
                decision = await session.pending_verdict

            if decision and decision.action == Action.BLOCK:
                session.state = SessionState.BLOCKED
                session.blocked_turns += 1
                logger.info(
                    "BLOCK: score=%.3f reason=%s (%d text + %d audio chunks dropped)",
                    decision.score, decision.reason,
                    len(pending_text), len(pending_audio),
                )
                reset_buffers()
                await ws.send_json({
                    "type": "blocked",
                    "seq": session.next_seq(),
                    "verdict": "BLOCKED",
                    "action": "BLOCKED",
                    "score": decision.score,
                    "reason": decision.reason,
                    "upstream": decision.verdict.layer if decision.verdict else "unknown",
                })
            elif session.transcript_buffer:
                session.state = SessionState.SAFE
                logger.info(
                    "ALLOW: flushing %d text + %d audio chunks",
                    len(pending_text), len(pending_audio),
                )
                await ws.send_json({
                    "type": "decision",
                    "seq": session.next_seq(),
                    "verdict": "SAFE",
                    "action": "SAFE",
                    "score": decision.score if decision else 0.0,
                })
                for text_chunk in pending_text:
                    await ws.send_json({
                        "type": "response_text",
                        "seq": session.next_seq(),
                        "delta": text_chunk,
                        "final": False,
                    })
                for audio_chunk in pending_audio:
                    await ws.send_bytes(audio_chunk)
                reset_buffers()
                await ws.send_json({
                    "type": "response_text",
                    "seq": session.next_seq(),
                    "final": True,
                })
            else:
                # No transcript this turn (silence / VAD glitch).
                reset_buffers()

            session.reset_turn()
            continue

        if sc.interrupted:
            logger.info("interrupted")
            reset_buffers()
