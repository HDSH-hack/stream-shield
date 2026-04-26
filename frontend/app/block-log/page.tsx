import { AppShell } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/layout/page-header";

const BlockLogPage = () => {
  return (
    <AppShell>
      <PageHeader
        eyebrow="Block Log"
        title="Inspect blocked events."
        description="Review attack patterns and trace guard decisions in real time."
        status="Live monitoring"
      />
    </AppShell>
  );
};

export default BlockLogPage;
