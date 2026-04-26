import { AppShell } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/layout/page-header";
import { GlassCard } from "@/components/ui/glass-card";
import { MetricCard } from "@/components/ui/metric-card";
import { PlaceholderPanel } from "@/components/ui/placeholder-panel";
import { SectionTitle } from "@/components/ui/section-title";
import { StatusBadge } from "@/components/ui/status-badge";
import { blockEvents, blockLogMetrics, selectedEvent } from "@/lib/mock-data";

const BlockLogPage = () => {
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
              <div
                key={`${event.time}-${event.session}`}
                className="grid grid-cols-[1fr_1fr_1fr] border-b border-white/10 p-4 text-sm last:border-b-0"
                >
                  <span className="text-white">{event.attackType}</span>
                  <span className="text-shield-muted">{event.session}</span>
                  <StatusBadge verdict={event.verdict} className="w-fit" />
                </div>
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
              <p>Upstream Leakage: 0 bytes</p>
            </div>
          </GlassCard>
          <GlassCard>
            <SectionTitle title="Chunk Trace" />
            <PlaceholderPanel className="h-40" />
          </GlassCard>
          <GlassCard>
            <SectionTitle title="Guard Decision Timeline" />
            <PlaceholderPanel className="h-24" />
          </GlassCard>
        </div>
      </div>
    </AppShell>
  );
};

export default BlockLogPage;
