"""FastAPI WebSocket server — Stream Shield entry point.

Architecture (hold-and-scan):
1. Client audio → Proxy → Gemini (auto-VAD, STT only)
2. Gemini inputTranscription → classifier
3. Auto-generated modelTurn → always discarded
4. If safe: send transcript as clientContent → relay new response to client
5. If blocked: send block notification to client

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
from stream_shield.guard.decision import Action
from stream_shield.buffer.manager import BufferManager
from stream_shield.policy import load_policy
from stream_shield.session import ShieldSession, SessionState

logger = logging.getLogger(__name__)

app = FastAPI(title="Stream Shield", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten in production
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
                client_to_gemini(ws, session, buffer_mgr),
                gemini_to_client(ws, session, buffer_mgr),
            )
    except WebSocketDisconnect:
        logger.info("client disconnected: %s", session_id)
    except Exception as e:
        logger.exception("session error: %s", session_id)
        if ws.client_state == WebSocketState.CONNECTED:
            await ws.send_json({"type": "error", "message": str(e)})
            await ws.close()


async def client_to_gemini(ws, session: ShieldSession, buffer_mgr):
    """Browser → backend → Gemini Live.

    Forward audio to Gemini for STT (auto-VAD).
    """
    while True:
        msg = await ws.receive()

        if msg.get("type") == "websocket.disconnect":
            break

        # Binary frame → audio PCM, forward to Gemini for STT
        if "bytes" in msg and msg["bytes"]:
            await session.upstream.send_realtime_input(
                audio=types.Blob(
                    mime_type="audio/pcm;rate=16000",
                    data=msg["bytes"],
                ),
            )

        # Text frame → JSON control message
        elif "text" in msg and msg["text"]:
            try:
                data = json.loads(msg["text"])
            except json.JSONDecodeError:
                continue

            if data.get("type") == "interrupt":
                logger.info("client interrupt")


async def gemini_to_client(ws, session: ShieldSession, buffer_mgr: BufferManager):
    """Gemini Live → backend → browser.

    Flow per turn:
    1. Receive inputTranscription (STT) from auto-VAD
    2. Discard auto-generated modelTurn (from audio input)
    3. Classify transcript
    4. If safe: send transcript as clientContent → relay NEW response
    5. If blocked: send block notification
    """
    async for msg in session.upstream.receive():
        sc = msg.server_content
        if sc is None:
            continue

        # --- inputTranscription: classify and decide ---
        if sc.input_transcription and sc.input_transcription.text:
            transcript = sc.input_transcription.text
            logger.info("transcript: %r", transcript[:80])

            await ws.send_json({
                "type": "transcript",
                "text": transcript,
            })

            # Classify
            session.state = SessionState.JUDGING
            decision = await buffer_mgr.classify_transcript(session, transcript)

            if decision.action == Action.ALLOW:
                # Safe → send transcript to Gemini as text, get response
                session.state = SessionState.SAFE
                logger.info("ALLOW (score=%.3f) — sending to Gemini", decision.score)

                await ws.send_json({
                    "type": "decision",
                    "decision": "ALLOW",
                    "score": decision.score,
                })

                # Send classified text to Gemini for response generation
                await session.upstream.send_client_content(
                    turns=[types.Content(
                        role="user",
                        parts=[types.Part(text=transcript)],
                    )],
                    turn_complete=True,
                )
                # Response will arrive as modelTurn below and be relayed

            else:
                # Blocked → notify client, skip response
                session.state = SessionState.BLOCKED
                session.blocked_turns += 1
                logger.info("BLOCK (score=%.3f reason=%s)", decision.score, decision.reason)

                await ws.send_json({
                    "type": "blocked",
                    "category": "prompt_injection",
                    "score": decision.score,
                    "reason": decision.reason,
                    "layer": decision.verdict.layer if decision.verdict else "unknown",
                    "transcript": transcript[:200],
                })

        # --- modelTurn: relay only when state is SAFE ---
        if sc.model_turn and sc.model_turn.parts:
            if session.state == SessionState.SAFE:
                for part in sc.model_turn.parts:
                    if part.inline_data and part.inline_data.data:
                        await ws.send_bytes(part.inline_data.data)
                    if part.text:
                        await ws.send_json({
                            "type": "response_text",
                            "delta": part.text,
                        })
            # JUDGING / BLOCKED / RELAYING → discard modelTurn

        # --- turnComplete ---
        if sc.turn_complete:
            if session.state == SessionState.SAFE:
                await ws.send_json({"type": "turn_complete"})
            logger.info("turn complete (state=%s, total=%d, blocked=%d)",
                        session.state.value, session.total_turns, session.blocked_turns)
            session.reset_turn()

        # --- interrupted ---
        if sc.interrupted:
            logger.info("turn interrupted")
            session.reset_turn()
