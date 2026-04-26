import { AppShell } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/layout/page-header";

const PlaygroundPage = () => {
  return (
    <AppShell>
      <PageHeader
        eyebrow="Attack Playground"
        title="Simulate split-stream attacks."
        description="Scenario controls and animated chunk flow will live here."
        status="Sandbox ready"
      />
    </AppShell>
  );
};

export default PlaygroundPage;
