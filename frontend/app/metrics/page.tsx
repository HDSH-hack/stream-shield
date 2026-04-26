import { AppShell } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/layout/page-header";
import { GlassCard } from "@/components/ui/glass-card";
import { MetricCard } from "@/components/ui/metric-card";
import { SectionTitle } from "@/components/ui/section-title";
import { verdictTextClass } from "@/components/ui/status-badge";
import {
  latencyBins,
  metricsCards,
  modelSummary,
  recentEvaluationRows,
  trafficBreakdown,
} from "@/lib/mock-data";

const performanceSeries = [
  { label: "12:00", recall: 72, precision: 81 },
  { label: "13:00", recall: 78, precision: 84 },
  { label: "14:00", recall: 83, precision: 86 },
  { label: "15:00", recall: 81, precision: 89 },
  { label: "16:00", recall: 88, precision: 91 },
  { label: "17:00", recall: 91, precision: 93 },
  { label: "Now", recall: 92, precision: 94 },
];

const attackCategoryLegend = [
  { label: "prompt_injection", value: "41%", color: "bg-shield-cyan" },
  { label: "jailbreak", value: "27%", color: "bg-shield-safe" },
  { label: "split_stream", value: "19%", color: "bg-shield-hold" },
  { label: "obfuscated", value: "13%", color: "bg-shield-blocked" },
];

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
          <div className="mb-4 flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
            <SectionTitle title="Detection Performance Over Time" />
            <div className="flex gap-3 text-xs text-shield-muted">
              <span className="inline-flex items-center gap-2">
                <span className="h-2 w-2 rounded-full bg-shield-cyan" />
                Recall
              </span>
              <span className="inline-flex items-center gap-2">
                <span className="h-2 w-2 rounded-full bg-shield-safe" />
                Precision
              </span>
            </div>
          </div>
          <div className="grid h-64 grid-cols-[auto_1fr] gap-3 rounded-xl border border-white/10 bg-white/[0.02] p-4">
            <div className="flex flex-col justify-between py-1 text-[10px] text-shield-muted">
              <span>100%</span>
              <span>75%</span>
              <span>50%</span>
              <span>25%</span>
            </div>
            <div className="flex items-end gap-3">
              {performanceSeries.map((point) => (
                <div
                  key={point.label}
                  className="flex flex-1 flex-col items-center justify-end gap-2"
                >
                  <div className="flex h-48 w-full items-end justify-center gap-1">
                    <div
                      className="w-1/3 rounded-t-lg bg-shield-cyan/85 shadow-[0_0_18px_rgba(34,211,238,0.18)]"
                      style={{ height: `${point.recall}%` }}
                    />
                    <div
                      className="w-1/3 rounded-t-lg bg-shield-safe/80 shadow-[0_0_18px_rgba(52,211,153,0.14)]"
                      style={{ height: `${point.precision}%` }}
                    />
                  </div>
                  <span className="text-[10px] text-shield-muted">{point.label}</span>
                </div>
              ))}
            </div>
          </div>
        </GlassCard>
        <GlassCard className="min-h-80">
          <div className="mb-4 flex items-start justify-between gap-4">
            <SectionTitle title="Latency Distribution" />
            <div className="rounded-xl border border-white/10 bg-white/[0.03] px-3 py-2 text-right">
              <p className="text-[10px] uppercase tracking-[0.16em] text-shield-muted">
                p95
              </p>
              <p className="text-sm font-semibold text-white">137ms</p>
            </div>
          </div>
          <div className="flex h-56 items-end gap-2 rounded-xl border border-white/10 bg-white/[0.02] p-4">
            {latencyBins.map((bin) => (
              <div
                key={bin.label}
                className="flex flex-1 flex-col items-center justify-end gap-2"
              >
                <div
                  className="w-full rounded-t-md bg-shield-safe/80 shadow-[0_0_16px_rgba(52,211,153,0.12)]"
                  style={{ height: `${bin.value}%` }}
                />
                <span className="text-[10px] text-shield-muted">{bin.label}</span>
              </div>
            ))}
          </div>
          <div className="mt-4 grid grid-cols-4 gap-2 text-center text-xs">
            {[
              ["Avg", "58ms"],
              ["p50", "49ms"],
              ["p95", "137ms"],
              ["Max", "204ms"],
            ].map(([label, value]) => (
              <div key={label} className="rounded-xl bg-white/[0.03] px-2 py-2">
                <p className="text-shield-muted">{label}</p>
                <p className="mt-1 font-semibold text-white">{value}</p>
              </div>
            ))}
          </div>
        </GlassCard>
      </div>

      <div className="mt-4 grid gap-4 lg:grid-cols-3">
        <GlassCard>
          <SectionTitle title="Attack Categories" />
          <div className="grid gap-4 md:grid-cols-[auto_1fr]">
            <div className="grid h-40 w-40 place-items-center rounded-full bg-[conic-gradient(from_180deg,#22D3EE_0_41%,#34D399_41%_68%,#FBBF24_68%_87%,#FB7185_87%_100%)]">
              <div className="grid h-24 w-24 place-items-center rounded-full bg-shield-panel text-sm font-semibold text-white">
                4 types
              </div>
            </div>
            <div className="grid content-center gap-2">
              {attackCategoryLegend.map((item) => (
                <div
                  key={item.label}
                  className="flex items-center justify-between gap-3 text-xs"
                >
                  <span className="inline-flex items-center gap-2 text-shield-muted">
                    <span className={`h-2.5 w-2.5 rounded-full ${item.color}`} />
                    {item.label}
                  </span>
                  <span className="font-semibold text-white">{item.value}</span>
                </div>
              ))}
            </div>
          </div>
        </GlassCard>
        <GlassCard>
          <SectionTitle title="Traffic Breakdown" />
          <div className="space-y-3">
            {trafficBreakdown.map((item) => (
              <div key={item.label}>
                <div className="mb-1 flex justify-between text-xs text-shield-muted">
                  <span className={verdictTextClass[item.verdict]}>{item.label}</span>
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
          <div className="grid grid-cols-[1.4fr_repeat(4,0.7fr)] border-b border-white/10 bg-white/[0.04] p-3 text-xs font-semibold uppercase tracking-[0.12em] text-shield-muted">
            <span>Category</span>
            <span>Recall</span>
            <span>Precision</span>
            <span>FPR</span>
            <span>Latency</span>
          </div>
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
