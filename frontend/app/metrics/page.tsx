import { AppShell } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/layout/page-header";
import { GlassCard } from "@/components/ui/glass-card";
import { MetricCard } from "@/components/ui/metric-card";
import { PlaceholderPanel } from "@/components/ui/placeholder-panel";
import { SectionTitle } from "@/components/ui/section-title";
import { metricsCards, modelSummary } from "@/lib/mock-data";

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
          <PlaceholderPanel className="h-56" />
        </GlassCard>
        <GlassCard className="min-h-80">
          <SectionTitle title="Latency Distribution" />
          <PlaceholderPanel className="h-56" />
        </GlassCard>
      </div>

      <div className="mt-4 grid gap-4 lg:grid-cols-3">
        <GlassCard>
          <SectionTitle title="Attack Categories" />
          <PlaceholderPanel className="h-40" />
        </GlassCard>
        <GlassCard>
          <SectionTitle title="Traffic Breakdown" />
          <PlaceholderPanel className="h-40" />
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
    </AppShell>
  );
};

export default MetricsPage;
