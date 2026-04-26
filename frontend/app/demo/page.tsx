import { AppShell } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/layout/page-header";

const DemoPage = () => {
  return (
    <AppShell>
      <PageHeader
        eyebrow="Live Demo Dashboard"
        title="Blocked before Gemini"
        description="The dashboard screen will show live input, guard decisions, upstream delivery, metrics, and block logs."
        status="Connected to Gemini Live API"
      />
    </AppShell>
  );
};

export default DemoPage;
