import type { Verdict } from "@/lib/mock-data";

export type ShieldConnectionState =
  | "idle"
  | "connecting"
  | "connected"
  | "fallback"
  | "error";

export type ShieldDecisionEvent = {
  type: "decision" | "blocked";
  seq?: number;
  verdict?: Verdict;
  action?: Verdict;
  score?: number;
  reason?: string;
  upstream?: string;
};

export type ShieldSessionStartedEvent = {
  type: "session_started";
  session_id: string;
  policy_id: string;
};

export type ShieldErrorEvent = {
  type: "error";
  message: string;
};

export type ShieldTranscriptEvent = {
  type: "transcript" | "input_transcript";
  seq?: number;
  text: string;
  final?: boolean;
};

export type ShieldModelResponseEvent = {
  type: "model_response" | "response_text";
  seq?: number;
  text?: string;
  delta?: string;
  final?: boolean;
};

export type ShieldAudioResponseEvent = {
  type: "response_audio";
  seq?: number;
  mimeType?: string;
  format?: string;
  data?: string;
  final?: boolean;
};

export type ShieldServerEvent =
  | ShieldDecisionEvent
  | ShieldSessionStartedEvent
  | ShieldErrorEvent
  | ShieldTranscriptEvent
  | ShieldModelResponseEvent
  | ShieldAudioResponseEvent;

export type ShieldAudioChunkMessage = {
  type: "realtimeInput.audio";
  sessionId: string;
  seq: number;
  mimeType: "audio/pcm;rate=16000";
  sampleRate: 16000;
  data: string;
};

export const getShieldWsUrl = (sessionId: string, policy = "default") => {
  const base =
    process.env.NEXT_PUBLIC_STREAM_SHIELD_WS_URL ??
    "ws://127.0.0.1:8000/ws";
  return `${base}/${sessionId}?policy=${policy}`;
};

export const parseShieldEvent = (raw: string): ShieldServerEvent | null => {
  try {
    const parsed = JSON.parse(raw) as Partial<ShieldServerEvent>;
    if (
      parsed.type === "decision" ||
      parsed.type === "blocked" ||
      parsed.type === "session_started" ||
      parsed.type === "error" ||
      parsed.type === "transcript" ||
      parsed.type === "input_transcript" ||
      parsed.type === "model_response" ||
      parsed.type === "response_text" ||
      parsed.type === "response_audio"
    ) {
      return parsed as ShieldServerEvent;
    }
    return null;
  } catch {
    return null;
  }
};
