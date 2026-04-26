"""FastAPI WebSocket server — Stream Shield entry point.

Accepts a browser WebSocket connection, opens a Gemini Live API session
with auto-VAD, and runs the layered guard pipeline between them.

See UNIFIED_DESIGN.md §3 for full architecture.
"""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Annotated

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Path
from fastapi.middleware.cors import CORSMiddleware

from stream_shield.gemini import connect_gemini
from stream_shield.guard.engine import GuardEngine
from stream_shield.buffer.manager import BufferManager
from stream_shield.policy import load_policy
from stream_shield.session import ShieldSession
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
            await asyncio.gather(
                client_to_gemini(ws, session, buffer_mgr),
                gemini_to_client(ws, session, buffer_mgr),
            )
    except WebSocketDisconnect:
        logger.info("client disconnected")
    except Exception as e:
        logger.exception("session error")
        await ws.send_json({"type": "error", "message": str(e)})
        await ws.close()


async def client_to_gemini(ws, session, buffer_mgr):
    """Browser → backend → Gemini Live."""
    while True:
        msg = await ws.receive()
        # TODO: handle audio bytes vs json control
        # See protocol.py for message handling.
        ...


async def gemini_to_client(ws, session, buffer_mgr):
    """Gemini Live → backend → browser.
    Includes Response Buffer (~100ms delay) for parallel pipeline."""
    while True:
        # TODO: drain Gemini WS, push transcripts and modelTurn chunks
        ...
