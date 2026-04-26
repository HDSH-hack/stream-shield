"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Activity, Github, ShieldCheck } from "lucide-react";

import { cn } from "@/lib/cn";

const navItems = [
  { href: "/demo", label: "Demo" },
  { href: "/playground", label: "Playground" },
  { href: "/metrics", label: "Metrics" },
  { href: "/block-log", label: "Block Log" },
  { href: "/architecture", label: "Architecture" },
];

const isActiveRoute = (pathname: string, href: string) => {
  if (href === "/") {
    return pathname === "/";
  }
  return pathname === href || pathname.startsWith(`${href}/`);
};

export const TopNav = () => {
  const pathname = usePathname();

  return (
    <header className="sticky top-0 z-40 border-b border-white/10 bg-shield-bg/78 backdrop-blur-xl">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-6">
        <Link href="/" className="flex items-center gap-3">
          <span className="grid h-9 w-9 place-items-center rounded-xl border border-shield-cyan/40 bg-shield-cyan/10 text-shield-cyan shadow-glow">
            <ShieldCheck size={19} />
          </span>
          <span className="text-sm font-semibold tracking-wide text-white">
            Stream Shield
          </span>
        </Link>

        <nav className="hidden items-center gap-1 rounded-full border border-white/10 bg-white/[0.03] p-1 md:flex">
          {navItems.map((item) => {
            const active = isActiveRoute(pathname, item.href);
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "rounded-full px-3 py-1.5 text-xs font-medium transition",
                  active
                    ? "bg-shield-cyan/14 text-shield-cyan"
                    : "text-shield-muted hover:bg-white/[0.06] hover:text-white",
                )}
              >
                {item.label}
              </Link>
            );
          })}
        </nav>

        <div className="flex items-center gap-2">
          <div className="hidden items-center gap-2 rounded-full border border-shield-safe/20 bg-shield-safe/10 px-3 py-1.5 text-xs font-medium text-shield-safe sm:flex">
            <Activity size={13} />
            Demo ready
          </div>
          <a
            href="https://github.com"
            aria-label="GitHub"
            className="grid h-9 w-9 place-items-center rounded-xl border border-white/10 bg-white/[0.03] text-shield-muted transition hover:text-white"
          >
            <Github size={16} />
          </a>
        </div>
      </div>
    </header>
  );
};
