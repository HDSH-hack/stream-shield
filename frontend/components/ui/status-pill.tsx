import { cn } from "@/lib/cn";

type StatusPillProps = {
  children: React.ReactNode;
  tone?: "safe" | "info" | "hold" | "blocked" | "neutral";
  className?: string;
};

const toneClasses = {
  safe: "border-shield-safe/20 bg-shield-safe/10 text-shield-safe",
  info: "border-shield-cyan/25 bg-shield-cyan/10 text-shield-cyan",
  hold: "border-shield-hold/25 bg-shield-hold/10 text-shield-hold",
  blocked: "border-shield-blocked/25 bg-shield-blocked/10 text-shield-blocked",
  neutral: "border-white/10 bg-white/[0.03] text-shield-muted",
};

export const StatusPill = ({
  children,
  tone = "safe",
  className,
}: StatusPillProps) => {
  return (
    <span
      className={cn(
        "inline-flex w-fit items-center gap-2 rounded-full border px-3 py-1.5 text-xs font-medium",
        toneClasses[tone],
        className,
      )}
    >
      {children}
    </span>
  );
};
