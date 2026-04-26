"""FastAPI WebSocket server — Stream Shield entry point.

Architecture (VAD-respecting parallel pipeline):
1. Client audio (JSON base64) → Proxy → Gemini (auto-VAD, STT)
2. inputTranscription → classifier in background during auto-response
3. Auto-response discarded, turnComplete waited (VAD respected)
4. Safe → clientContent(transcript) → relay response to client
5. Blocked → send block notification

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
            await asyncio.gather(
                _handle_client(ws, session, buffer_mgr),
                _handle_gemini(ws, session, buffer_mgr),
            )
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
                try:
                    pcm = base64.b64decode(b64)
                except Exception:
                    await ws.send_json({
                        "type": "error",
                        "message": "invalid base64 audio chunk",
                    })
                    continue

                mime_type = data.get("mimeType") or "audio/pcm;rate=16000"
                await session.upstream.send_realtime_input(
                    audio=types.Blob(mime_type=mime_type, data=pcm),
                )



# ---------------------------------------------------------------------------
# Gemini → Client
# ---------------------------------------------------------------------------

async def _handle_gemini(ws, session: ShieldSession, buffer_mgr: BufferManager):
    """Handle Gemini Live events, apply guard, relay to frontend.

    Per-turn flow (audio path, VAD-respecting):
    Phase 1: auto-VAD runs. inputTranscription → classify in background.
             Auto-response modelTurn → discard. Wait for turnComplete.
    Phase 2: safe → send clientContent → relay response.
             blocked → send block event.
    """
    async for msg in session.upstream.receive():
        sc = msg.server_content
        if sc is None:
            continue

        # --- Phase 1: inputTranscription → classify ---
        if sc.input_transcription and sc.input_transcription.text:
            transcript = sc.input_transcription.text
            logger.info("transcript: %r", transcript[:80])
            session.transcript_buffer = transcript
            session.state = SessionState.JUDGING

            await ws.send_json({
                "type": "transcript",
                "seq": session.next_seq(),
                "text": transcript,
                "final": True,
            })

            session.pending_verdict = asyncio.create_task(
                buffer_mgr.classify(session, transcript)
            )

        # --- Phase 1: auto-response modelTurn → discard ---
        if sc.model_turn and session.state in (SessionState.RELAYING, SessionState.JUDGING):
            pass

        # --- Phase 1 end: turnComplete → Phase 2 ---
        if sc.turn_complete and session.state in (SessionState.RELAYING, SessionState.JUDGING):
            decision = None
            if session.pending_verdict:
                decision = await session.pending_verdict

            if decision and decision.action == Action.BLOCK:
                session.state = SessionState.BLOCKED
                session.blocked_turns += 1
                logger.info("BLOCK: score=%.3f reason=%s", decision.score, decision.reason)

                await ws.send_json({
                    "type": "blocked",
                    "seq": session.next_seq(),
                    "verdict": "BLOCKED",
                    "action": "BLOCKED",
                    "score": decision.score,
                    "reason": decision.reason,
                    "upstream": decision.verdict.layer if decision.verdict else "unknown",
                })
                session.reset_turn()

            elif session.transcript_buffer:
                session.state = SessionState.SAFE
                logger.info("ALLOW: sending transcript as clientContent")

                await ws.send_json({
                    "type": "decision",
                    "seq": session.next_seq(),
                    "verdict": "SAFE",
                    "action": "SAFE",
                    "score": decision.score if decision else 0.0,
                })

                await session.upstream.send_client_content(
                    turns=[types.Content(
                        role="user",
                        parts=[types.Part(text=session.transcript_buffer)],
                    )],
                    turn_complete=True,
                )
            else:
                session.reset_turn()
            continue

        # --- Phase 2: relay clientContent response ---
        if sc.model_turn and session.state == SessionState.SAFE:
            for part in sc.model_turn.parts or []:
                if part.text:
                    await ws.send_json({
                        "type": "response_text",
                        "seq": session.next_seq(),
                        "delta": part.text,
                        "final": False,
                    })
                if part.inline_data and part.inline_data.data:
                    audio_b64 = base64.b64encode(part.inline_data.data).decode("ascii")
                    await ws.send_json({
                        "type": "response_audio",
                        "seq": session.next_seq(),
                        "mimeType": getattr(part.inline_data, "mime_type", None),
                        "data": audio_b64,
                        "final": False,
                    })

        # --- Phase 2: response turnComplete ---
        if sc.turn_complete and session.state == SessionState.SAFE:
            logger.info("response turn complete (total=%d, blocked=%d)",
                        session.total_turns, session.blocked_turns)
            await ws.send_json({
                "type": "response_text",
                "seq": session.next_seq(),
                "final": True,
            })
            session.reset_turn()

        if sc.turn_complete and session.state == SessionState.BLOCKED:
            session.reset_turn()

        if sc.interrupted:
            logger.info("interrupted")
