import { cn } from "@/lib/cn";

type GlassCardProps = {
  children: React.ReactNode;
  className?: string;
};

export const GlassCard = ({ children, className }: GlassCardProps) => {
  return (
    <section
      className={cn(
        "relative overflow-hidden rounded-2xl border border-white/10 bg-[linear-gradient(180deg,rgba(17,24,39,0.86),rgba(13,20,32,0.72))] p-5 shadow-[0_18px_70px_rgba(0,0,0,0.32)] backdrop-blur",
        "before:pointer-events-none before:absolute before:inset-x-0 before:top-0 before:h-px before:bg-gradient-to-r before:from-transparent before:via-shield-cyan/45 before:to-transparent",
        className,
      )}
    >
      <div className="relative">{children}</div>
    </section>
  );
};
