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

export type ShieldTextChunkMessage = {
  type: "realtimeInput.text";
  sessionId: string;
  scenario: string;
  seq: number;
  text: string;
};

export const getShieldWsUrl = (sessionId: string, policy = "default") => {
  const base =
    process.env.NEXT_PUBLIC_STREAM_SHIELD_WS_URL ??
    "ws://127.0.0.1:8000/ws";
  return `${base}/${sessionId}?policy=${policy}`;
};

export const parseShieldDecision = (raw: string): ShieldDecisionEvent | null => {
  try {
    const parsed = JSON.parse(raw) as Partial<ShieldDecisionEvent>;
    if (parsed.type !== "decision" && parsed.type !== "blocked") {
      return null;
    }
    return parsed as ShieldDecisionEvent;
  } catch {
    return null;
  }
};
