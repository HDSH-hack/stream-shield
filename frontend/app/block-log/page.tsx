"use client";

import { useMemo, useState } from "react";

import { AppShell } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/layout/page-header";
import { GlassCard } from "@/components/ui/glass-card";
import { MetricCard } from "@/components/ui/metric-card";
import { SectionTitle } from "@/components/ui/section-title";
import { StatusBadge } from "@/components/ui/status-badge";
import {
  blockEvents,
  blockLogMetrics,
  chunkTraceByEvent,
} from "@/lib/mock-data";

const BlockLogPage = () => {
  const [selectedEventId, setSelectedEventId] = useState(blockEvents[0].id);
  const selectedEvent =
    blockEvents.find((event) => event.id === selectedEventId) ?? blockEvents[0];
  const selectedTrace = useMemo(
    () => chunkTraceByEvent[selectedEvent.id] ?? [],
    [selectedEvent.id],
  );

  return (
    <AppShell>
      <PageHeader
        eyebrow="Block Log"
        title="Inspect blocked events."
        description="Review attack patterns and trace guard decisions in real time."
        status="Live monitoring"
      />
      <div className="grid gap-4 md:grid-cols-4">
        {blockLogMetrics.map((metric) => (
          <MetricCard key={metric.label} metric={metric} />
        ))}
      </div>

      <div className="mt-4 grid gap-4 lg:grid-cols-[1.35fr_0.65fr]">
        <GlassCard className="min-h-[32rem]">
          <SectionTitle
            title="Event Stream"
            description="Search, filter, and inspect recent guard decisions."
          />
          <div className="mb-4 grid gap-3 md:grid-cols-[1fr_auto_auto_auto]">
            <div className="h-10 rounded-xl border border-white/10 bg-white/[0.03]" />
            <div className="h-10 w-32 rounded-xl border border-white/10 bg-white/[0.03]" />
            <div className="h-10 w-32 rounded-xl border border-white/10 bg-white/[0.03]" />
            <div className="h-10 w-32 rounded-xl border border-white/10 bg-white/[0.03]" />
          </div>
          <div className="rounded-xl border border-white/10">
            {blockEvents.map((event) => (
              <button
                key={event.id}
                type="button"
                onClick={() => setSelectedEventId(event.id)}
                className={
                  event.id === selectedEvent.id
                    ? "grid w-full grid-cols-[auto_1fr_1fr_auto] items-center gap-3 border-b border-shield-cyan/20 bg-shield-cyan/10 p-4 text-left text-sm last:border-b-0"
                    : "grid w-full grid-cols-[auto_1fr_1fr_auto] items-center gap-3 border-b border-white/10 p-4 text-left text-sm transition last:border-b-0 hover:bg-white/[0.04]"
                }
              >
                <span className="font-mono text-xs text-shield-muted">{event.time}</span>
                <span className="text-white">{event.attackType}</span>
                <span className="text-shield-muted">{event.session}</span>
                <StatusBadge verdict={event.verdict} className="w-fit" />
              </button>
              ))}
          </div>
        </GlassCard>

        <div className="grid gap-4">
          <GlassCard>
            <SectionTitle title="Selected Event" />
            <div className="space-y-2 text-sm text-shield-muted">
              <p>Session ID: {selectedEvent.session}</p>
              <p>Verdict: {selectedEvent.verdict}</p>
              <p>Score: {selectedEvent.score.toFixed(2)}</p>
              <p>Attack Type: {selectedEvent.attackType}</p>
              <p>Preview: {selectedEvent.preview}</p>
              <p>Upstream Leakage: 0 bytes</p>
            </div>
          </GlassCard>
          <GlassCard>
            <SectionTitle title="Chunk Trace" />
            <div className="space-y-2">
              {selectedTrace.map((chunk) => (
                <div
                  key={chunk.label}
                  className="grid grid-cols-[auto_1fr_auto] items-center gap-3 rounded-xl border border-white/10 bg-white/[0.03] p-3 text-sm"
                >
                  <span className="text-xs text-shield-muted">{chunk.label}</span>
                  <span className="truncate font-mono text-xs text-white">
                    {chunk.preview}
                  </span>
                  <StatusBadge verdict={chunk.verdict} />
                </div>
              ))}
            </div>
          </GlassCard>
          <GlassCard>
            <SectionTitle title="Guard Decision Timeline" />
            <div className="flex h-24 items-center gap-2">
              {selectedTrace.map((chunk) => (
                <div
                  key={`${chunk.label}-timeline`}
                  className={
                    chunk.verdict === "BLOCKED"
                      ? "h-3 flex-1 rounded-full bg-shield-blocked"
                      : chunk.verdict === "HOLD"
                        ? "h-3 flex-1 rounded-full bg-shield-hold"
                        : "h-3 flex-1 rounded-full bg-shield-safe"
                  }
                />
              ))}
            </div>
          </GlassCard>
        </div>
      </div>
    </AppShell>
  );
};

export default BlockLogPage;
