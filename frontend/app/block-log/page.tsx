import { AppShell } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/layout/page-header";
import { GlassCard } from "@/components/ui/glass-card";
import { SectionTitle } from "@/components/ui/section-title";

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
        {[
          ["Total Events", "1,284"],
          ["Blocked Events", "217"],
          ["Active Sessions", "42"],
          ["Mean Response Time", "61ms"],
        ].map(([label, value]) => (
          <GlassCard key={label} className="p-4">
            <p className="text-xs text-shield-muted">{label}</p>
            <p className="mt-2 text-2xl font-bold text-white">{value}</p>
          </GlassCard>
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
            {["prompt_injection", "korean_jailbreak", "normal_chat", "split_stream"].map(
              (row) => (
                <div
                  key={row}
                  className="grid grid-cols-[1fr_1fr_1fr] border-b border-white/10 p-4 text-sm last:border-b-0"
                >
                  <span className="text-white">{row}</span>
                  <span className="text-shield-muted">sess-a13f</span>
                  <span className="text-shield-blocked">blocked</span>
                </div>
              ),
            )}
          </div>
        </GlassCard>

        <div className="grid gap-4">
          <GlassCard>
            <SectionTitle title="Selected Event" />
            <div className="space-y-2 text-sm text-shield-muted">
              <p>Session ID: sess-a13f</p>
              <p>Verdict: BLOCKED</p>
              <p>Score: 0.93</p>
              <p>Upstream Leakage: 0 bytes</p>
            </div>
          </GlassCard>
          <GlassCard>
            <SectionTitle title="Chunk Trace" />
            <div className="h-40 rounded-xl border border-dashed border-white/15 bg-white/[0.02]" />
          </GlassCard>
          <GlassCard>
            <SectionTitle title="Guard Decision Timeline" />
            <div className="h-24 rounded-xl border border-dashed border-white/15 bg-white/[0.02]" />
          </GlassCard>
        </div>
      </div>
    </AppShell>
  );
};

export default BlockLogPage;
