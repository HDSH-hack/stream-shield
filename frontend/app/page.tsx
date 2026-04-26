import Link from "next/link";
import { ArrowRight, Zap } from "lucide-react";

import { AppShell } from "@/components/layout/app-shell";
import { streamRows } from "@/lib/mock-data";

const Home = () => {
  return (
    <AppShell className="flex min-h-[calc(100vh-4rem)] flex-col">
      <section className="grid flex-1 items-center gap-10 py-10 lg:grid-cols-[1fr_0.88fr]">
        <div>
          <div className="mb-5 inline-flex items-center gap-2 rounded-full border border-shield-cyan/30 bg-shield-cyan/10 px-3 py-1 text-xs font-medium text-shield-cyan">
            <Zap size={14} />
            Real-time input guard for Gemini Live API
          </div>
          <h1 className="max-w-4xl text-5xl font-bold leading-tight text-white md:text-7xl">
            Stop malicious streams before they reach Gemini Live.
          </h1>
          <p className="mt-6 max-w-2xl text-lg leading-8 text-shield-muted">
            Stream Shield intercepts streaming input, classifies rolling chunks
            with local open-source models, and blocks prompt injection before it
            reaches the upstream model.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Link
              href="/demo"
              className="inline-flex items-center gap-2 rounded-xl bg-shield-cyan px-5 py-3 text-sm font-semibold text-slate-950 shadow-glow"
            >
              Launch Live Demo <ArrowRight size={16} />
            </Link>
            <Link
              href="/architecture"
              className="inline-flex items-center gap-2 rounded-xl border border-shield-border bg-white/5 px-5 py-3 text-sm font-semibold text-white"
            >
              View Architecture
            </Link>
          </div>
        </div>

        <div className="rounded-3xl border border-shield-border bg-shield-panel/80 p-5 shadow-glow backdrop-blur">
          <div className="mb-5 flex items-center justify-between">
            <span className="text-sm font-semibold">Stream Flow</span>
            <span className="rounded-full bg-shield-safe/10 px-3 py-1 text-xs font-medium text-shield-safe">
              Connected
            </span>
          </div>
          <div className="space-y-3 font-mono text-sm">
            {streamRows.slice(0, 4).map((row) => (
              <div
                key={`${row.input}-${row.score}`}
                className="grid grid-cols-[1fr_auto_auto] items-center gap-3 rounded-2xl border border-white/10 bg-white/[0.03] px-4 py-3"
              >
                <span className="truncate text-slate-200">{row.input}</span>
                <span
                  className={
                    row.verdict === "BLOCKED"
                      ? "text-shield-blocked"
                      : row.verdict === "HOLD"
                        ? "text-shield-hold"
                        : "text-shield-safe"
                  }
                >
                  {row.verdict} {row.score.toFixed(2)}
                </span>
                <span className="text-shield-muted">{row.upstream}</span>
              </div>
            ))}
          </div>
          <div className="mt-5 rounded-2xl border border-shield-blocked/30 bg-shield-blocked/10 px-4 py-3 text-sm font-semibold text-shield-blocked">
            Blocked before Gemini
          </div>
        </div>
      </section>
    </AppShell>
  );
};

export default Home;
