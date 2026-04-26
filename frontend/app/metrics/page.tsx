import { AppShell } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/layout/page-header";
import { GlassCard } from "@/components/ui/glass-card";
import { SectionTitle } from "@/components/ui/section-title";

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
        {[
          ["Attack Recall", "91.7%", "up vs last run"],
          ["False Positive Rate", "3.2%", "down vs last run"],
          ["Avg Guard Latency", "58ms", "p95 137ms"],
          ["Bytes Leaked", "0", "No upstream leakage"],
        ].map(([label, value, note]) => (
          <GlassCard key={label} className="p-4">
            <p className="text-xs text-shield-muted">{label}</p>
            <p className="mt-2 text-2xl font-bold text-white">{value}</p>
            <p className="mt-1 text-xs text-shield-muted">{note}</p>
          </GlassCard>
        ))}
      </div>

      <div className="mt-4 grid gap-4 lg:grid-cols-[1.35fr_0.65fr]">
        <GlassCard className="min-h-80">
          <SectionTitle title="Detection Performance Over Time" />
          <div className="h-56 rounded-xl border border-dashed border-white/15 bg-white/[0.02]" />
        </GlassCard>
        <GlassCard className="min-h-80">
          <SectionTitle title="Latency Distribution" />
          <div className="h-56 rounded-xl border border-dashed border-white/15 bg-white/[0.02]" />
        </GlassCard>
      </div>

      <div className="mt-4 grid gap-4 lg:grid-cols-3">
        <GlassCard>
          <SectionTitle title="Attack Categories" />
          <div className="h-40 rounded-xl border border-dashed border-white/15 bg-white/[0.02]" />
        </GlassCard>
        <GlassCard>
          <SectionTitle title="Traffic Breakdown" />
          <div className="h-40 rounded-xl border border-dashed border-white/15 bg-white/[0.02]" />
        </GlassCard>
        <GlassCard>
          <SectionTitle title="Model Summary" />
          <div className="space-y-2 text-sm text-shield-muted">
            <p>Active model: Prompt Guard 2 86M</p>
            <p>Inference: local</p>
            <p>Classification API cost: $0</p>
          </div>
        </GlassCard>
      </div>
    </AppShell>
  );
};

export default MetricsPage;
