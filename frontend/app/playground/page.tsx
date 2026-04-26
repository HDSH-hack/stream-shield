import { AppShell } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/layout/page-header";
import { GlassCard } from "@/components/ui/glass-card";
import { SectionTitle } from "@/components/ui/section-title";
import {
  attackScenarios,
  expectedGuardBehavior,
  playgroundFilters,
  simulationControls,
  splitStreamChunks,
} from "@/lib/mock-data";

const PlaygroundPage = () => {
  return (
    <AppShell>
      <PageHeader
        eyebrow="Attack Playground"
        title="Simulate split-stream attacks."
        description="Scenario controls and animated chunk flow will live here."
        status="Sandbox ready"
      />
      <div className="grid gap-4 lg:grid-cols-[0.85fr_1.15fr]">
        <GlassCard className="min-h-[34rem]">
          <SectionTitle
            title="Attack Scenarios"
            description="Choose the stream pattern to simulate."
          />
          <div className="mb-4 flex flex-wrap gap-2 text-xs">
            {playgroundFilters.map((filter) => (
              <span
                key={filter}
                className="rounded-full border border-white/10 bg-white/[0.03] px-3 py-1 text-shield-muted"
              >
                {filter}
              </span>
            ))}
          </div>
          <div className="grid gap-3">
            {attackScenarios.map((scenario) => (
              <div
                key={scenario.name}
                className="rounded-xl border border-white/10 bg-white/[0.03] p-4 text-sm text-white"
              >
                <p>{scenario.name}</p>
                <p className="mt-1 text-xs text-shield-muted">{scenario.category}</p>
              </div>
            ))}
          </div>
        </GlassCard>

        <div className="grid gap-4">
          <GlassCard>
            <SectionTitle
              title="Simulation Controls"
              description="Chunk interval, buffer size, overlap tail, and model."
            />
            <div className="grid gap-3 md:grid-cols-2">
              {simulationControls.map((control) => (
                <div
                  key={control.label}
                  className="rounded-xl border border-white/10 bg-white/[0.03] p-4"
                >
                  <p className="text-xs text-shield-muted">{control.label}</p>
                  <p className="mt-3 text-sm font-semibold text-white">
                    {control.value}
                  </p>
                </div>
              ))}
            </div>
          </GlassCard>

          <GlassCard>
            <SectionTitle
              title="Chunk Flow"
              description="The stream is evaluated across chunk boundaries."
            />
            <div className="grid gap-3 md:grid-cols-4">
              {splitStreamChunks.map((chunk) => (
                <div
                  key={chunk}
                  className="min-h-20 rounded-xl border border-shield-cyan/20 bg-shield-cyan/5 p-3 font-mono text-xs text-shield-cyan"
                >
                  {chunk}
                </div>
              ))}
            </div>
          </GlassCard>

          <GlassCard>
            <SectionTitle title="Expected Guard Behavior" />
            <div className="rounded-xl border border-shield-blocked/20 bg-shield-blocked/10 p-4 text-sm font-semibold text-shield-blocked">
              {expectedGuardBehavior
                .map((item) => `${item.verdict} ${item.score.toFixed(2)}`)
                .join(" → ")}
              . Blocked before Gemini.
            </div>
          </GlassCard>
        </div>
      </div>
    </AppShell>
  );
};

export default PlaygroundPage;
