import type { MetricCardData } from "@/lib/mock-data";

import { GlassCard } from "@/components/ui/glass-card";

type MetricCardProps = {
  metric: MetricCardData;
};

export const MetricCard = ({ metric }: MetricCardProps) => {
  return (
    <GlassCard className="p-4">
      <div className="mb-3 flex items-center justify-between">
        <p className="text-xs font-medium uppercase tracking-[0.16em] text-shield-muted">
          {metric.label}
        </p>
        <span className="h-2 w-2 rounded-full bg-shield-cyan shadow-[0_0_14px_rgba(34,211,238,0.8)]" />
      </div>
      <p className="text-3xl font-bold tracking-tight text-white">{metric.value}</p>
      {metric.note ? (
        <p className="mt-1 text-xs text-shield-muted">{metric.note}</p>
      ) : null}
    </GlassCard>
  );
};
