import type { Verdict } from "@/lib/mock-data";
import { cn } from "@/lib/cn";

type StatusBadgeProps = {
  verdict: Verdict;
  className?: string;
};

const statusClasses: Record<Verdict, string> = {
  SAFE: "border-shield-safe/25 bg-shield-safe/10 text-shield-safe",
  HOLD: "border-shield-hold/25 bg-shield-hold/10 text-shield-hold",
  BLOCKED: "border-shield-blocked/25 bg-shield-blocked/10 text-shield-blocked",
};

export const StatusBadge = ({ verdict, className }: StatusBadgeProps) => {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full border px-2.5 py-1 text-xs font-semibold",
        statusClasses[verdict],
        className,
      )}
    >
      {verdict}
    </span>
  );
};

export const verdictTextClass: Record<Verdict, string> = {
  SAFE: "text-shield-safe",
  HOLD: "text-shield-hold",
  BLOCKED: "text-shield-blocked",
};

export const verdictPanelClass: Record<Verdict, string> = {
  SAFE: "border-shield-safe/20 bg-shield-safe/10 text-shield-safe",
  HOLD: "border-shield-hold/20 bg-shield-hold/10 text-shield-hold",
  BLOCKED: "border-shield-blocked/20 bg-shield-blocked/10 text-shield-blocked",
};
