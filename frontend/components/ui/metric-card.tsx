import type { MetricCardData } from "@/lib/mock-data";

import { GlassCard } from "@/components/ui/glass-card";

type MetricCardProps = {
  metric: MetricCardData;
};

export const MetricCard = ({ metric }: MetricCardProps) => {
  return (
    <GlassCard className="p-4">
      <p className="text-xs text-shield-muted">{metric.label}</p>
      <p className="mt-2 text-2xl font-bold text-white">{metric.value}</p>
      {metric.note ? (
        <p className="mt-1 text-xs text-shield-muted">{metric.note}</p>
      ) : null}
    </GlassCard>
  );
};
