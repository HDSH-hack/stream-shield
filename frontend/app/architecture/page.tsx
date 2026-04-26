import { AppShell } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/layout/page-header";

const ArchitecturePage = () => {
  return (
    <AppShell>
      <PageHeader
        eyebrow="Architecture"
        title="Client to proxy to guard to Gemini Live API."
        description="How Stream Shield intercepts, classifies, and blocks malicious input before it reaches Gemini Live API."
        status="System design"
      />
    </AppShell>
  );
};

export default ArchitecturePage;
