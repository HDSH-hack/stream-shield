import { cn } from "@/lib/cn";

type PlaceholderPanelProps = {
  className?: string;
};

export const PlaceholderPanel = ({ className }: PlaceholderPanelProps) => {
  return (
    <div
      className={cn(
        "rounded-xl border border-dashed border-white/15 bg-white/[0.02]",
        className,
      )}
    />
  );
};
