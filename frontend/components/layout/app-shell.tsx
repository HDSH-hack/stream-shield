import { TopNav } from "@/components/layout/top-nav";
import { cn } from "@/lib/cn";

type AppShellProps = {
  children: React.ReactNode;
  className?: string;
};

export const AppShell = ({ children, className }: AppShellProps) => {
  return (
    <div className="relative min-h-screen overflow-hidden bg-shield-bg text-slate-100">
      <div className="pointer-events-none fixed inset-0 bg-[radial-gradient(circle_at_18%_8%,rgba(34,211,238,0.16),transparent_28rem),radial-gradient(circle_at_85%_14%,rgba(52,211,153,0.08),transparent_28rem)]" />
      <div className="pointer-events-none fixed inset-0 bg-[linear-gradient(rgba(148,163,184,0.05)_1px,transparent_1px),linear-gradient(90deg,rgba(148,163,184,0.05)_1px,transparent_1px)] bg-[size:44px_44px] opacity-40 [mask-image:linear-gradient(to_bottom,black,transparent_78%)]" />
      <TopNav />
      <main className={cn("relative mx-auto max-w-7xl px-6 py-10", className)}>
        {children}
      </main>
    </div>
  );
};
