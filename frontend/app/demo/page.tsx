import { AppShell } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/layout/page-header";
import { GlassCard } from "@/components/ui/glass-card";
import { MetricCard } from "@/components/ui/metric-card";
import { PlaceholderPanel } from "@/components/ui/placeholder-panel";
import { SectionTitle } from "@/components/ui/section-title";
import {
  GuardDecisionRow,
  StreamInputRow,
  UpstreamRow,
} from "@/components/ui/stream-row";
import { dashboardMetrics, streamRows } from "@/lib/mock-data";

const DemoPage = () => {
  return (
    <AppShell>
      <PageHeader
        eyebrow="Live Demo Dashboard"
        title="Blocked before Gemini"
        description="The dashboard screen will show live input, guard decisions, upstream delivery, metrics, and block logs."
        status="Connected to Gemini Live API"
      />
      <div className="grid gap-4 md:grid-cols-4">
        {dashboardMetrics.map((metric) => (
          <MetricCard key={metric.label} metric={metric} />
        ))}
      </div>

      <div className="mt-4 grid gap-4 lg:grid-cols-3">
        <GlassCard className="min-h-80">
          <SectionTitle
            title="User Input Stream"
            description="Incoming chunks from browser or demo client."
          />
          <div className="space-y-3 font-mono text-sm text-shield-muted">
            {streamRows.slice(0, 3).map((row) => (
              <StreamInputRow key={`${row.time}-${row.input}`} row={row} />
            ))}
          </div>
        </GlassCard>

        <GlassCard className="min-h-80">
          <SectionTitle
            title="Shield Guard"
            description="Rolling-buffer decisions before upstream release."
          />
          <div className="space-y-3 font-mono text-sm">
            {streamRows.slice(0, 3).map((row) => (
              <GuardDecisionRow key={`${row.verdict}-${row.score}`} row={row} />
            ))}
          </div>
        </GlassCard>

        <GlassCard className="min-h-80">
          <SectionTitle
            title="Gemini Live API"
            description="Only safe chunks are forwarded upstream."
          />
          <div className="space-y-3 font-mono text-sm text-shield-muted">
            {streamRows.slice(0, 3).map((row) => (
              <UpstreamRow key={`${row.upstream}-${row.input}`} row={row} />
            ))}
          </div>
        </GlassCard>
      </div>

      <div className="mt-4 grid gap-4 lg:grid-cols-2">
        <GlassCard>
          <SectionTitle title="Attack Playground" description="Scenario launch area." />
          <PlaceholderPanel className="h-28" />
        </GlassCard>
        <GlassCard>
          <SectionTitle title="Block Log" description="Recent guard events." />
          <PlaceholderPanel className="h-28" />
        </GlassCard>
      </div>
    </AppShell>
  );
};

export default DemoPage;
