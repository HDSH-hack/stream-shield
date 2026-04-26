import type { StreamFlowRow } from "@/lib/mock-data";

import { cn } from "@/lib/cn";
import { verdictPanelClass, verdictTextClass } from "@/components/ui/status-badge";

type StreamInputRowProps = {
  row: StreamFlowRow;
};

export const StreamInputRow = ({ row }: StreamInputRowProps) => {
  return (
    <div className="rounded-xl border border-white/10 bg-white/[0.035] p-3 shadow-[inset_0_1px_0_rgba(255,255,255,0.04)]">
      <span className="mr-3 text-[11px] text-shield-muted">{row.time}</span>
      <span>{row.input}</span>
    </div>
  );
};

export const GuardDecisionRow = ({ row }: StreamInputRowProps) => {
  return (
    <div className={cn("rounded-xl border p-3", verdictPanelClass[row.verdict])}>
      {row.verdict} {row.score.toFixed(2)} {row.guardNote}
    </div>
  );
};

export const UpstreamRow = ({ row }: StreamInputRowProps) => {
  return (
    <div
      className={
        row.upstream === "not forwarded"
          ? "rounded-xl border border-shield-blocked/25 bg-shield-blocked/10 p-3 font-semibold text-shield-blocked shadow-[0_0_22px_rgba(251,113,133,0.08)]"
          : "rounded-xl border border-white/10 bg-white/[0.035] p-3"
      }
    >
      {row.upstream}
    </div>
  );
};

export const CompactStreamRow = ({ row }: StreamInputRowProps) => {
  return (
    <div className="grid grid-cols-[1fr_auto_auto] items-center gap-3 rounded-2xl border border-white/10 bg-white/[0.04] px-4 py-3 shadow-[inset_0_1px_0_rgba(255,255,255,0.04)]">
      <span className="truncate text-slate-200">{row.input}</span>
      <span className={verdictTextClass[row.verdict]}>
        {row.verdict} {row.score.toFixed(2)}
      </span>
      <span className="text-shield-muted">{row.upstream}</span>
    </div>
  );
};
