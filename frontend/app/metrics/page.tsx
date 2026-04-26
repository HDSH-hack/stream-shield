import { AppShell } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/layout/page-header";
import { GlassCard } from "@/components/ui/glass-card";
import { MetricCard } from "@/components/ui/metric-card";
import { SectionTitle } from "@/components/ui/section-title";
import {
  latencyBins,
  metricsCards,
  modelSummary,
  recentEvaluationRows,
  trafficBreakdown,
} from "@/lib/mock-data";

const MetricsPage = () => {
  return (
    <AppShell>
      <PageHeader
        eyebrow="Metrics"
        title="Detection and latency metrics."
        description="Track detection performance, latency, and guard effectiveness over time."
        status="Live analytics"
      />
      <div className="grid gap-4 md:grid-cols-4">
        {metricsCards.map((metric) => (
          <MetricCard key={metric.label} metric={metric} />
        ))}
      </div>

      <div className="mt-4 grid gap-4 lg:grid-cols-[1.35fr_0.65fr]">
        <GlassCard className="min-h-80">
          <SectionTitle title="Detection Performance Over Time" />
          <div className="flex h-56 items-end gap-3 rounded-xl border border-white/10 bg-white/[0.02] p-4">
            {[72, 78, 83, 81, 88, 91, 92].map((value, index) => (
              <div key={`${value}-${index}`} className="flex flex-1 flex-col justify-end">
                <div
                  className="rounded-t-lg bg-shield-cyan/80"
                  style={{ height: `${value}%` }}
                />
              </div>
            ))}
          </div>
        </GlassCard>
        <GlassCard className="min-h-80">
          <SectionTitle title="Latency Distribution" />
          <div className="flex h-56 items-end gap-2 rounded-xl border border-white/10 bg-white/[0.02] p-4">
            {latencyBins.map((bin) => (
              <div key={bin.label} className="flex flex-1 flex-col items-center justify-end gap-2">
                <div
                  className="w-full rounded-t-md bg-shield-safe/80"
                  style={{ height: `${bin.value}%` }}
                />
                <span className="text-[10px] text-shield-muted">{bin.label}</span>
              </div>
            ))}
          </div>
        </GlassCard>
      </div>

      <div className="mt-4 grid gap-4 lg:grid-cols-3">
        <GlassCard>
          <SectionTitle title="Attack Categories" />
          <div className="grid h-40 place-items-center rounded-xl border border-white/10 bg-[conic-gradient(from_180deg,#22D3EE_0_41%,#34D399_41%_68%,#FBBF24_68%_87%,#FB7185_87%_100%)]">
            <div className="grid h-24 w-24 place-items-center rounded-full bg-shield-panel text-sm font-semibold text-white">
              4 types
            </div>
          </div>
        </GlassCard>
        <GlassCard>
          <SectionTitle title="Traffic Breakdown" />
          <div className="space-y-3">
            {trafficBreakdown.map((item) => (
              <div key={item.label}>
                <div className="mb-1 flex justify-between text-xs text-shield-muted">
                  <span>{item.label}</span>
                  <span>{item.value}%</span>
                </div>
                <div className="h-3 overflow-hidden rounded-full bg-white/[0.06]">
                  <div
                    className={
                      item.verdict === "SAFE"
                        ? "h-full rounded-full bg-shield-safe"
                        : item.verdict === "HOLD"
                          ? "h-full rounded-full bg-shield-hold"
                          : "h-full rounded-full bg-shield-blocked"
                    }
                    style={{ width: `${item.value}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </GlassCard>
        <GlassCard>
          <SectionTitle title="Model Summary" />
          <div className="space-y-2 text-sm text-shield-muted">
            {modelSummary.map((item) => (
              <p key={item}>{item}</p>
            ))}
          </div>
        </GlassCard>
      </div>
      <GlassCard className="mt-4">
        <SectionTitle title="Recent Evaluation Results" />
        <div className="overflow-hidden rounded-xl border border-white/10">
          {recentEvaluationRows.map((row) => (
            <div
              key={row.category}
              className="grid grid-cols-[1.4fr_repeat(4,0.7fr)] border-b border-white/10 p-3 text-sm last:border-b-0"
            >
              <span className="text-white">{row.category}</span>
              <span className="text-shield-muted">{row.recall}</span>
              <span className="text-shield-muted">{row.precision}</span>
              <span className="text-shield-muted">{row.fpr}</span>
              <span className="text-shield-muted">{row.latency}</span>
            </div>
          ))}
        </div>
      </GlassCard>
    </AppShell>
  );
};

export default MetricsPage;
