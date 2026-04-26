import { AppShell } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/layout/page-header";
import { GlassCard } from "@/components/ui/glass-card";
import { SectionTitle } from "@/components/ui/section-title";
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
          <GlassCard key={metric.label} className="p-4">
            <p className="text-xs text-shield-muted">{metric.label}</p>
            <p className="mt-2 text-2xl font-bold text-white">{metric.value}</p>
          </GlassCard>
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
              <div key={`${row.time}-${row.input}`} className="rounded-xl bg-white/[0.03] p-3">
                {row.time} {row.input}
              </div>
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
              <div
                key={`${row.verdict}-${row.score}`}
                className={
                  row.verdict === "BLOCKED"
                    ? "rounded-xl border border-shield-blocked/20 bg-shield-blocked/10 p-3 text-shield-blocked"
                    : row.verdict === "HOLD"
                      ? "rounded-xl border border-shield-hold/20 bg-shield-hold/10 p-3 text-shield-hold"
                      : "rounded-xl border border-shield-safe/20 bg-shield-safe/10 p-3 text-shield-safe"
                }
              >
                {row.verdict} {row.score.toFixed(2)} {row.guardNote}
              </div>
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
              <div
                key={`${row.upstream}-${row.input}`}
                className={
                  row.upstream === "not forwarded"
                    ? "rounded-xl border border-shield-blocked/20 bg-shield-blocked/10 p-3 font-semibold text-shield-blocked"
                    : "rounded-xl bg-white/[0.03] p-3"
                }
              >
                {row.upstream}
              </div>
            ))}
          </div>
        </GlassCard>
      </div>

      <div className="mt-4 grid gap-4 lg:grid-cols-2">
        <GlassCard>
          <SectionTitle title="Attack Playground" description="Scenario launch area." />
          <div className="h-28 rounded-xl border border-dashed border-white/15 bg-white/[0.02]" />
        </GlassCard>
        <GlassCard>
          <SectionTitle title="Block Log" description="Recent guard events." />
          <div className="h-28 rounded-xl border border-dashed border-white/15 bg-white/[0.02]" />
        </GlassCard>
      </div>
    </AppShell>
  );
};

export default DemoPage;
