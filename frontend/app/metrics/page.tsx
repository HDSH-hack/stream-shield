import { AppShell } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/layout/page-header";

const MetricsPage = () => {
  return (
    <AppShell>
      <PageHeader
        eyebrow="Metrics"
        title="Detection and latency metrics."
        description="Track detection performance, latency, and guard effectiveness over time."
        status="Live analytics"
      />
    </AppShell>
  );
};

export default MetricsPage;
