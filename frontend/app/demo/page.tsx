import { AppShell } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/layout/page-header";
import { GlassCard } from "@/components/ui/glass-card";
import { MetricCard } from "@/components/ui/metric-card";
import { SectionTitle } from "@/components/ui/section-title";
import { StatusBadge } from "@/components/ui/status-badge";
import {
  GuardDecisionRow,
  StreamInputRow,
  UpstreamRow,
} from "@/components/ui/stream-row";
import {
  blockEvents,
  dashboardMetrics,
  splitStreamChunks,
  streamRows,
} from "@/lib/mock-data";

const DemoPage = () => {
  return (
    <AppShell>
      <PageHeader
        eyebrow="Live Demo Dashboard"
        title="Blocked before Gemini"
        description="Frontend dashboard for live input, guard decisions, upstream delivery, metrics, and block logs."
        status="Backend interface ready"
      />
      <div className="grid gap-4 md:grid-cols-4">
        {dashboardMetrics.map((metric) => (
          <MetricCard key={metric.label} metric={metric} />
        ))}
      </div>

      <div className="mt-4 grid gap-4 lg:grid-cols-[1fr_auto_1fr_auto_1fr]">
        <GlassCard className="min-h-80">
          <SectionTitle
            title="User Input Stream"
            description="Incoming chunks from browser or demo client."
          />
          <div className="space-y-3 font-mono text-sm text-shield-muted">
            {streamRows.map((row) => (
              <StreamInputRow key={`${row.time}-${row.input}`} row={row} />
            ))}
          </div>
        </GlassCard>

        <div className="hidden items-center justify-center lg:flex">
          <div className="h-px w-10 bg-gradient-to-r from-shield-cyan/20 to-shield-cyan" />
        </div>

        <GlassCard className="min-h-80">
          <SectionTitle
            title="Shield Guard"
            description="Rolling-buffer decisions before upstream release."
          />
          <div className="space-y-3 font-mono text-sm">
            {streamRows.map((row) => (
              <GuardDecisionRow key={`${row.verdict}-${row.score}`} row={row} />
            ))}
          </div>
        </GlassCard>

        <div className="hidden items-center justify-center lg:flex">
          <div className="h-px w-10 bg-gradient-to-r from-shield-cyan/20 to-shield-cyan" />
        </div>

        <GlassCard className="min-h-80">
          <SectionTitle
            title="Gemini Live API"
            description="Only safe chunks are forwarded upstream."
          />
          <div className="space-y-3 font-mono text-sm text-shield-muted">
            {streamRows.map((row) => (
              <UpstreamRow key={`${row.upstream}-${row.input}`} row={row} />
            ))}
          </div>
        </GlassCard>
      </div>

      <div className="mt-4 grid gap-4 lg:grid-cols-2">
        <GlassCard>
          <SectionTitle
            title="Attack Playground"
            description="Selected preset: Split-stream Injection"
          />
          <div className="grid grid-cols-4 gap-2 font-mono text-xs">
            {splitStreamChunks.map((chunk, index) => (
              <div
                key={chunk}
                className={
                  index === splitStreamChunks.length - 1
                    ? "rounded-xl border border-shield-blocked/25 bg-shield-blocked/10 p-3 text-shield-blocked"
                    : "rounded-xl border border-shield-cyan/20 bg-shield-cyan/5 p-3 text-shield-cyan"
                }
              >
                {chunk}
              </div>
            ))}
          </div>
        </GlassCard>
        <GlassCard>
          <SectionTitle title="Block Log" description="Recent guard events." />
          <div className="space-y-2">
            {blockEvents.slice(0, 3).map((event) => (
              <div
                key={`${event.time}-${event.session}`}
                className="grid grid-cols-[auto_1fr_auto] items-center gap-3 rounded-xl border border-white/10 bg-white/[0.03] p-3 text-sm"
              >
                <span className="font-mono text-xs text-shield-muted">{event.time}</span>
                <span className="truncate text-white">{event.attackType}</span>
                <StatusBadge verdict={event.verdict} />
              </div>
            ))}
          </div>
        </GlassCard>
      </div>
    </AppShell>
  );
};

export default DemoPage;
