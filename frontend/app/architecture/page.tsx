import { AppShell } from "@/components/layout/app-shell";
import { Fragment } from "react";
import { PageHeader } from "@/components/layout/page-header";
import { GlassCard } from "@/components/ui/glass-card";
import { SectionTitle } from "@/components/ui/section-title";
import { StatusPill } from "@/components/ui/status-pill";
import {
  architectureBranches,
  architectureNodes,
  modelSummary,
  observabilityOutputs,
} from "@/lib/mock-data";

const ArchitecturePage = () => {
  return (
    <AppShell>
      <PageHeader
        eyebrow="Architecture"
        title="Client to proxy to guard to Gemini Live API."
        description="How Stream Shield intercepts, classifies, and blocks malicious input before it reaches Gemini Live API."
        status="System design"
      />
      <GlassCard>
        <SectionTitle
          title="Main Architecture Flow"
          description="Only safe chunks continue upstream."
        />
        <div className="grid gap-3 lg:grid-cols-[repeat(13,minmax(0,1fr))]">
          {architectureNodes.map((node, index) => (
            <Fragment key={node.title}>
              <div
                className={
                  index === architectureNodes.length - 1
                    ? "min-h-36 rounded-xl border border-shield-safe/25 bg-shield-safe/10 p-4 text-sm font-semibold text-white shadow-[0_0_28px_rgba(52,211,153,0.12)]"
                    : index === 5
                      ? "min-h-36 rounded-xl border border-shield-cyan/35 bg-shield-cyan/10 p-4 text-sm font-semibold text-white shadow-glow"
                      : "min-h-36 rounded-xl border border-shield-cyan/20 bg-shield-cyan/5 p-4 text-sm font-semibold text-white"
                }
              >
                <span className="mb-3 block font-mono text-xs text-shield-muted">
                  0{index + 1}
                </span>
                <span>{node.title}</span>
                <p className="mt-3 text-xs font-normal leading-5 text-shield-muted">
                  {node.description}
                </p>
              </div>
              {index < architectureNodes.length - 1 ? (
                <div
                  className="hidden items-center lg:flex"
                >
                  <div className="h-px w-full bg-gradient-to-r from-shield-cyan/20 via-shield-cyan to-shield-cyan/20" />
                </div>
              ) : null}
            </Fragment>
          ))}
        </div>
      </GlassCard>

      <div className="mt-4 grid gap-4 lg:grid-cols-3">
        {architectureBranches.map((branch) => (
          <GlassCard key={branch.title}>
            <SectionTitle title={branch.title} />
            <div
              className={
                branch.tone === "blocked"
                  ? "rounded-xl border border-shield-blocked/20 bg-shield-blocked/10 p-4 text-sm font-semibold text-shield-blocked"
                  : branch.tone === "safe"
                    ? "rounded-xl border border-shield-safe/20 bg-shield-safe/10 p-4 text-sm font-semibold text-shield-safe"
                    : "rounded-xl border border-shield-cyan/20 bg-shield-cyan/10 p-4 text-sm font-semibold text-shield-cyan"
              }
            >
              {branch.path}
            </div>
          </GlassCard>
        ))}
      </div>

      <div className="mt-4 grid gap-4 lg:grid-cols-[0.9fr_1.1fr]">
        <GlassCard>
          <SectionTitle title="Runtime Summary" />
          <div className="space-y-3 text-sm text-shield-muted">
            {modelSummary.slice(0, 3).map((item) => (
              <div
                key={item}
                className="rounded-xl border border-white/10 bg-white/[0.03] px-4 py-3"
              >
                {item}
              </div>
            ))}
          </div>
        </GlassCard>
        <GlassCard>
          <SectionTitle title="Observability + Outputs" />
          <div className="grid gap-3 sm:grid-cols-2">
            {observabilityOutputs.map((output) => (
              <div
                key={output}
                className="rounded-xl border border-white/10 bg-white/[0.03] p-4"
              >
                <StatusPill tone="info">{output}</StatusPill>
              </div>
            ))}
          </div>
        </GlassCard>
      </div>
    </AppShell>
  );
};

export default ArchitecturePage;
