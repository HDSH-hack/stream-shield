# Stream Shield Frontend / Backend Interface

This document describes the current frontend contract for the Stream Shield demo.
It is intentionally small and provisional so the backend can match it quickly,
then we can revise it once the final Gemini Live bridge is fixed.

## Transport

- Protocol: WebSocket
- Frontend env var: `NEXT_PUBLIC_STREAM_SHIELD_WS_URL`
- Default base URL: `ws://127.0.0.1:8000/ws`
- Runtime URL shape:

```text
{NEXT_PUBLIC_STREAM_SHIELD_WS_URL}/{sessionId}?policy={policy}
```

Current frontend defaults:

```text
ws://127.0.0.1:8000/ws/demo-session?policy=default
```

Backend should accept one WebSocket connection per active browser mic stream.
The frontend currently sends JSON messages only, including audio chunks as
base64 encoded PCM. Backend should also broadcast audio responses as JSON
`response_audio` events instead of binary frames for the demo UI.

## Frontend -> Backend

### Audio Chunk

Used by `/playground` when the user clicks `Start Mic Stream`.

```ts
type ShieldAudioChunkMessage = {
  type: "realtimeInput.audio";
  sessionId: string;
  seq: number;
  mimeType: "audio/pcm;rate=16000";
  sampleRate: 16000;
  data: string;
};
```

Audio format:

- Mono
- PCM16 little-endian
- 16 kHz sample rate
- Base64 encoded in `data`
- Current chunk duration: about 250 ms
- Current payload size: about 8000 bytes raw PCM before base64 per chunk

Example:

```json
{
  "type": "realtimeInput.audio",
  "sessionId": "demo-session",
  "seq": 12,
  "mimeType": "audio/pcm;rate=16000",
  "sampleRate": 16000,
  "data": "AAABAAIA..."
}
```

Expected backend behavior:

- Decode `data` from base64 to PCM16 bytes.
- Forward audio to Gemini Live or local STT path.
- Broadcast transcript events back to frontend.
- Broadcast guard decisions back to frontend.
- Broadcast model response text back to frontend.

## Backend -> Frontend

Frontend accepts these event types. Unknown event types are ignored.

### Session Started Event

Sent after the backend accepts the socket, loads policy, warms the guard, and
opens the Gemini Live session.

```ts
type ShieldSessionStartedEvent = {
  type: "session_started";
  session_id: string;
  policy_id: string;
};
```

Example:

```json
{
  "type": "session_started",
  "session_id": "demo-session",
  "policy_id": "default"
}
```

### Error Event

```ts
type ShieldErrorEvent = {
  type: "error";
  message: string;
};
```

Example:

```json
{
  "type": "error",
  "message": "GEMINI_API_KEY not set"
}
```

### Decision Event

```ts
type ShieldDecisionEvent = {
  type: "decision" | "blocked";
  seq?: number;
  verdict?: "SAFE" | "HOLD" | "BLOCKED";
  action?: "SAFE" | "HOLD" | "BLOCKED";
  score?: number;
  reason?: string;
  upstream?: string;
};
```

Notes:

- `seq` should match the text/audio chunk sequence when possible.
- Frontend reads `verdict` first, then falls back to `action`.
- Use `type: "blocked"` when the backend wants the UI to show a hard block.
- `score` should be normalized `0.0` to `1.0`.

Examples:

```json
{
  "type": "decision",
  "seq": 4,
  "verdict": "HOLD",
  "score": 0.56,
  "reason": "rolling buffer requires more context"
}
```

```json
{
  "type": "blocked",
  "seq": 8,
  "verdict": "BLOCKED",
  "score": 0.93,
  "reason": "prompt injection detected",
  "upstream": "prompt-guard-2"
}
```

### Transcript Event

```ts
type ShieldTranscriptEvent = {
  type: "transcript" | "input_transcript";
  seq?: number;
  text: string;
  final?: boolean;
};
```

Notes:

- Use `final: false` or omit `final` for partial transcripts.
- Use `final: true` when the transcript segment is complete.
- Frontend displays partial transcript as the current live transcript.
- Frontend appends final transcript to the transcript panel.

Example:

```json
{
  "type": "transcript",
  "seq": 15,
  "text": "ignore the previous instructions",
  "final": false
}
```

### Model Response Event

```ts
type ShieldModelResponseEvent = {
  type: "model_response" | "response_text";
  seq?: number;
  text?: string;
  delta?: string;
  final?: boolean;
};
```

Notes:

- Use `delta` for streaming response tokens/chunks.
- Use `text` for full response replacement or final response.
- Frontend appends deltas until a final response arrives.

Example:

```json
{
  "type": "response_text",
  "seq": 22,
  "delta": "I can help with that.",
  "final": false
}
```

### Audio Response Event

Used when Gemini Live emits an audio part. The backend base64-encodes the audio
so the frontend event stream remains JSON-only.

```ts
type ShieldAudioResponseEvent = {
  type: "response_audio";
  seq?: number;
  mimeType?: string;
  data?: string;
  final?: boolean;
};
```

Example:

```json
{
  "type": "response_audio",
  "seq": 23,
  "mimeType": "audio/pcm;rate=24000",
  "data": "AAABAAIA...",
  "final": false
}
```

## Connection Lifecycle

Current frontend behavior:

1. User opens `/playground`.
2. User selects an attack scenario as a spoken demo guide.
3. User clicks `Start Mic Stream`:
   - frontend opens a WebSocket
   - requests microphone permission
   - sends `realtimeInput.audio` chunks while streaming
   - displays transcript, model response, and decision events
4. User clicks `Stop Stream`:
   - frontend stops the mic recorder
   - frontend closes the WebSocket

Timeout / fallback:

- If the WebSocket does not open quickly, frontend shows fallback state.
- There is no text simulation fallback in the frontend contract.

## Implementation References

- Frontend WebSocket types: `frontend/lib/ws.ts`
- Frontend mic recorder: `frontend/lib/audio/recorder.ts`
- Frontend UI integration: `frontend/app/playground/page.tsx`

## Backend Checklist

- [ ] Accept `GET /ws/{sessionId}?policy={policy}` as a WebSocket endpoint.
- [ ] Parse JSON text frames.
- [ ] Handle `realtimeInput.audio` base64 PCM16 chunks.
- [ ] Broadcast `session_started` after Gemini Live is ready.
- [ ] Broadcast `error` for recoverable setup or protocol failures.
- [ ] Broadcast `transcript` or `input_transcript`.
- [ ] Broadcast `model_response` or `response_text`.
- [ ] Broadcast `response_audio` for Gemini audio chunks.
- [ ] Broadcast `decision` or `blocked`.
- [ ] Keep `seq` aligned where possible for UI correlation.

## Open Questions

- Whether final backend prefers JSON base64 audio or binary WebSocket frames.
- Whether `policy` should stay in query string or move into an initial session
  message.
- Whether Gemini Live response events should include richer metadata such as
  latency, model name, and guard stage.
