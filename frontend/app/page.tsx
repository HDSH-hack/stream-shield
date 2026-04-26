import Link from "next/link";
import { ArrowRight, Radio, Zap } from "lucide-react";

import { AppShell } from "@/components/layout/app-shell";
import { CompactStreamRow } from "@/components/ui/stream-row";
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
          <h1 className="max-w-4xl text-5xl font-bold leading-tight tracking-tight text-white md:text-7xl">
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

        <div className="relative rounded-3xl border border-shield-border bg-[linear-gradient(180deg,rgba(17,24,39,0.9),rgba(13,20,32,0.75))] p-5 shadow-glow backdrop-blur">
          <div className="pointer-events-none absolute -inset-px rounded-3xl bg-gradient-to-b from-shield-cyan/20 via-transparent to-shield-safe/10 opacity-70" />
          <div className="relative">
          <div className="mb-5 flex items-center justify-between">
            <span className="flex items-center gap-2 text-sm font-semibold text-white">
              <Radio size={16} className="text-shield-cyan" />
              Stream Flow
            </span>
            <span className="rounded-full bg-shield-safe/10 px-3 py-1 text-xs font-medium text-shield-safe">
              Connected
            </span>
          </div>
          <div className="space-y-3 font-mono text-sm">
            {streamRows.slice(0, 4).map((row) => (
              <CompactStreamRow key={`${row.input}-${row.score}`} row={row} />
            ))}
          </div>
          <div className="mt-5 rounded-2xl border border-shield-blocked/30 bg-shield-blocked/10 px-4 py-3 text-sm font-semibold text-shield-blocked">
            Blocked before Gemini
          </div>
          </div>
        </div>
      </section>
    </AppShell>
  );
};

export default Home;
