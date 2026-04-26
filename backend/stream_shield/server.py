"""FastAPI WebSocket server — Stream Shield entry point.

Architecture (VAD-respecting parallel pipeline):
1. Client audio → Proxy → Gemini (auto-VAD does STT + auto-response)
2. inputTranscription → start classifier in background
3. Auto-response modelTurn → discard, but let VAD flow complete naturally
4. Auto-response turnComplete → session clean
5. If safe: send transcript as clientContent → relay new response to client
6. If blocked: send block notification

See UNIFIED_DESIGN.md §3 for full architecture.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from typing import Annotated

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Path
from fastapi.middleware.cors import CORSMiddleware
from google.genai import types
from starlette.websockets import WebSocketState

from stream_shield.gemini import connect_gemini
from stream_shield.guard.engine import GuardEngine
from stream_shield.guard.decision import Action, Decision
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
    session_id: Annotated[str, Path(min_length=4, max_length=64)],
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
                client_to_gemini(ws, session),
                gemini_to_client(ws, session, buffer_mgr),
            )
    except WebSocketDisconnect:
        logger.info("client disconnected: %s", session_id)
    except Exception as e:
        logger.exception("session error: %s", session_id)
        if ws.client_state == WebSocketState.CONNECTED:
            await ws.send_json({"type": "error", "message": str(e)})
            await ws.close()


async def client_to_gemini(ws, session: ShieldSession):
    """Browser → backend → Gemini Live.

    Forward audio to Gemini for STT via auto-VAD.
    """
    while True:
        msg = await ws.receive()

        if msg.get("type") == "websocket.disconnect":
            break

        if "bytes" in msg and msg["bytes"]:
            await session.upstream.send_realtime_input(
                audio=types.Blob(
                    mime_type="audio/pcm;rate=16000",
                    data=msg["bytes"],
                ),
            )


async def gemini_to_client(ws, session: ShieldSession, buffer_mgr: BufferManager):
    """Gemini Live → backend → browser.

    Per-turn flow (VAD-respecting):
    Phase 1: Receive auto-VAD events. Classify transcript in background.
             Discard auto-response. Wait for turnComplete.
    Phase 2: If safe, send transcript as clientContent and relay response.
             If blocked, send block notification.
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

            await ws.send_json({"type": "transcript", "text": transcript})

            # Start classifier (runs in background during auto-response)
            session.pending_verdict = asyncio.create_task(
                buffer_mgr.classify(session, transcript)
            )

        # --- Phase 1: auto-response modelTurn → discard ---
        if sc.model_turn and session.state in (SessionState.RELAYING, SessionState.JUDGING):
            pass  # discard auto-response, let VAD flow complete

        # --- Phase 1 end: auto-response turnComplete → Phase 2 ---
        if sc.turn_complete and session.state in (SessionState.RELAYING, SessionState.JUDGING):
            # Ensure classifier is done
            decision = None
            if session.pending_verdict:
                decision = await session.pending_verdict

            if decision and decision.action == Action.BLOCK:
                # BLOCKED
                session.state = SessionState.BLOCKED
                session.blocked_turns += 1
                logger.info("BLOCK: score=%.3f reason=%s",
                            decision.score, decision.reason)
                await ws.send_json({
                    "type": "blocked",
                    "category": "prompt_injection",
                    "score": decision.score,
                    "reason": decision.reason,
                    "layer": decision.verdict.layer if decision.verdict else "unknown",
                    "transcript": session.transcript_buffer[:200],
                })
                await ws.send_json({
                    "type": "decision",
                    "decision": "BLOCK",
                    "score": decision.score,
                    "reason": decision.reason,
                })
            elif session.transcript_buffer:
                # SAFE → send transcript as clientContent for response
                session.state = SessionState.SAFE
                logger.info("ALLOW: sending transcript as clientContent")
                await ws.send_json({
                    "type": "decision",
                    "decision": "ALLOW",
                    "score": decision.score if decision else 0.0,
                })
                await session.upstream.send_client_content(
                    turns=[types.Content(
                        role="user",
                        parts=[types.Part(text=session.transcript_buffer)],
                    )],
                    turn_complete=True,
                )
                # Continue receiving — Phase 2 response will arrive as modelTurn
            else:
                # No transcript (VAD didn't detect speech)
                session.reset_turn()
            continue

        # --- Phase 2: relay clientContent response ---
        if sc.model_turn and session.state == SessionState.SAFE:
            for part in sc.model_turn.parts or []:
                if part.inline_data and part.inline_data.data:
                    await ws.send_bytes(part.inline_data.data)
                if part.text:
                    await ws.send_json({"type": "response_text", "delta": part.text})

        # --- Phase 2: response turnComplete ---
        if sc.turn_complete and session.state == SessionState.SAFE:
            logger.info("response turn complete (total=%d, blocked=%d)",
                        session.total_turns, session.blocked_turns)
            await ws.send_json({"type": "turn_complete"})
            session.reset_turn()

        # --- Phase 2: blocked turn cleanup ---
        if sc.turn_complete and session.state == SessionState.BLOCKED:
            session.reset_turn()

        if sc.interrupted:
            logger.info("interrupted")
