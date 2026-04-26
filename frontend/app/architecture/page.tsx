import { AppShell } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/layout/page-header";
import { GlassCard } from "@/components/ui/glass-card";
import { SectionTitle } from "@/components/ui/section-title";
import { architectureNodes, modelSummary, observabilityOutputs } from "@/lib/mock-data";

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
        <div className="grid gap-3 lg:grid-cols-7">
          {architectureNodes.map((node) => (
            <div
              key={node}
              className="min-h-28 rounded-xl border border-shield-cyan/20 bg-shield-cyan/5 p-4 text-sm font-semibold text-white"
            >
              {node}
            </div>
          ))}
        </div>
      </GlassCard>

      <div className="mt-4 grid gap-4 lg:grid-cols-3">
        <GlassCard>
          <SectionTitle title="Blocked Branch" />
          <div className="rounded-xl border border-shield-blocked/20 bg-shield-blocked/10 p-4 text-sm font-semibold text-shield-blocked">
            Policy Engine &rarr; Block + Warning &rarr; Blocked before Gemini
          </div>
        </GlassCard>
        <GlassCard>
          <SectionTitle title="Runtime Summary" />
          <div className="space-y-2 text-sm text-shield-muted">
            {modelSummary.slice(0, 3).map((item) => (
              <p key={item}>{item}</p>
            ))}
          </div>
        </GlassCard>
        <GlassCard>
          <SectionTitle title="Observability + Outputs" />
          <div className="grid gap-2 text-sm text-shield-muted">
            {observabilityOutputs.map((output) => (
              <p key={output}>{output}</p>
            ))}
          </div>
        </GlassCard>
      </div>
    </AppShell>
  );
};

export default ArchitecturePage;
