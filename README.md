# Stream Shield

Streaming PI (prompt-injection) shield for Gemini Live API.
Hackathon implementation — 9 hours to working demo.

## What it is

A WebSocket proxy that sits in front of Gemini Live API:
- Intercepts streaming text and audio input from the browser.
- Runs layered classifiers (rule pass → Prompt Guard 2 → optional LLM judge).
- Blocks malicious input *before* it reaches Gemini.
- Forwards safe input transparently and streams the model's response back.

See [`UNIFIED_DESIGN.md`](./UNIFIED_DESIGN.md) for full architecture.

## Layout

```
stream-shield/
├── UNIFIED_DESIGN.md            # single source of truth
├── README.md                    # this file
├── docker-compose.yml           # local dev
├── backend/                     # FastAPI WebSocket proxy
│   ├── stream_shield/
│   │   ├── server.py            # WS handler
│   │   ├── gemini.py            # Gemini Live client
│   │   ├── protocol.py          # message parsing
│   │   ├── session.py           # ShieldSession
│   │   ├── buffer/              # Hold→Scan→Release + Response Buffer
│   │   ├── guard/               # L0 rules / L1 classifier / L2 judge
│   │   ├── policy.py            # per-entity YAML
│   │   ├── receipt.py           # Ed25519 sign chain (stretch)
│   │   ├── metrics.py
│   │   └── eval/runner.py       # attackset eval
│   ├── config/policy.default.yaml
│   ├── datasets/attackset.yaml
│   └── notebooks/
│       ├── gemini_live_poc.ipynb        # phase 0 timing PoC
│       └── promptguard_benchmark.ipynb  # model selection
├── frontend/                    # Vite + React
│   └── src/
│       ├── pages/Home.tsx
│       ├── pages/Dashboard.tsx
│       ├── components/
│       ├── audio/recorder.ts    # AudioWorklet PCM 16kHz
│       └── api/ws.ts            # WebSocket client
├── sidecar/                     # (stretch) Ed25519 signing daemon
└── docs/
    ├── api.md
    └── individual-contributions/
        ├── eunjin.md
        ├── dohoon.md
        ├── soowon.md
        └── gihwang/             # design doc + diagrams + page mockups
```

## Quick start

### Backend
```bash
cd backend
uv venv && source .venv/bin/activate
uv pip install -r requirements.txt
export GEMINI_API_KEY=...
uvicorn stream_shield.server:app --reload --port 8000
```

### Frontend
```bash
cd frontend
pnpm install
pnpm dev
```

브라우저에서 `http://localhost:5173` 접속 → mic permission → demo.

## Contributors

- Eunjin (@foura1201) — design + classifier + buffer
- Gihwang (@hangole1999) — frontend mockups + parallel pipeline + diagrams
- Dohoon (@DoHoonKim8) — tiered cascade + policy-as-config
- Soowon (@swjng) — receipts + per-entity customization + comparison

## License

MIT (TBD).
