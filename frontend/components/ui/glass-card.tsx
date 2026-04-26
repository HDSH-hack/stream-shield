import { cn } from "@/lib/cn";

type GlassCardProps = {
  children: React.ReactNode;
  className?: string;
};

export const GlassCard = ({ children, className }: GlassCardProps) => {
  return (
    <section
      className={cn(
        "rounded-2xl border border-white/10 bg-shield-panel/72 p-5 shadow-[0_18px_70px_rgba(0,0,0,0.28)] backdrop-blur",
        className,
      )}
    >
      {children}
    </section>
  );
};
