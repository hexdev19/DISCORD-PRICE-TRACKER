"use client";

import { useState, type ReactNode } from "react";
import {
  Crosshair,
  Settings2,
  Terminal,
  Eye,
  Check,
  Pause,
  RefreshCw,
  Hash,
  AtSign,
  BellPlus,
} from "lucide-react";
import { Reveal } from "./reveal";
import { TrackerMark } from "./logo";
import { cn } from "@/lib/utils";

type IconType = typeof Crosshair;

function Cell({
  label,
  value,
  accent,
}: {
  label: string;
  value: string;
  accent?: boolean;
}) {
  return (
    <div className="bg-ink p-3">
      <p className="font-mono text-[0.6rem] uppercase tracking-[0.14em] text-faint">
        {label}
      </p>
      <p className={cn("tnum mt-1 text-sm", accent ? "text-cyan" : "text-fg")}>
        {value}
      </p>
    </div>
  );
}

function StatusLine({ icon: Icon, children }: { icon: IconType; children: string }) {
  return (
    <div className="flex items-center gap-2 font-mono text-xs uppercase tracking-[0.16em] text-cyan">
      <Icon className="h-3.5 w-3.5" />
      {children}
    </div>
  );
}

function Product() {
  return (
    <p className="mt-3 text-base font-semibold text-fg">
      Sony WH-1000XM5 Wireless
    </p>
  );
}

const HELP_ROWS = [
  { cmd: "/track <url>", desc: "start watching a product" },
  { cmd: "/list", desc: "your active watches" },
  { cmd: "/info <id>", desc: "full detail + price chart" },
  { cmd: "/watch <id> threshold", desc: "set a target price" },
  { cmd: "/untrack <id>", desc: "stop watching" },
  { cmd: "/config show", desc: "view server setup" },
];

type Entry = { cmd: string; arg: string; output: ReactNode };

const DATA: Record<string, Entry> = {
  track: {
    cmd: "/track",
    arg: "url: amazon.com/…/wh-1000xm5",
    output: (
      <>
        <StatusLine icon={Check}>Tracking started</StatusLine>
        <Product />
        <div className="mt-2 flex items-end gap-3">
          <span className="tnum text-2xl font-semibold text-fg">$349.99</span>
          <span className="mb-1 font-mono text-[0.65rem] uppercase tracking-[0.14em] text-cyan">
            in stock
          </span>
        </div>
        <div className="mt-4 grid grid-cols-2 gap-px border border-line bg-line">
          <Cell label="Watch ID" value="u7X2B3C" />
          <Cell label="Store" value="Amazon · US" />
          <Cell label="Alerts" value="drop · restock" accent />
          <Cell label="Target" value="not set" />
        </div>
      </>
    ),
  },
  config: {
    cmd: "/config",
    arg: "show",
    output: (
      <>
        <StatusLine icon={Settings2}>Server config</StatusLine>
        <div className="mt-4 grid grid-cols-2 gap-px border border-line bg-line">
          <Cell label="Tracker role" value="@deal-team" />
          <Cell label="Alert channel" value="#deal-alerts" />
          <Cell label="Mention role" value="@deal-hunters" />
          <Cell label="Region" value="US" />
          <Cell label="Watches" value="12 / 25" accent />
          <Cell label="Status" value="ready" accent />
        </div>
      </>
    ),
  },
  help: {
    cmd: "/help",
    arg: "",
    output: (
      <>
        <StatusLine icon={Terminal}>Commands</StatusLine>
        <ul className="mt-4 border border-line">
          {HELP_ROWS.map((h) => (
            <li
              key={h.cmd}
              className="flex flex-col gap-0.5 border-b border-line px-4 py-2.5 last:border-0 sm:flex-row sm:items-baseline sm:gap-3"
            >
              <span className="tnum shrink-0 text-sm text-cyan">{h.cmd}</span>
              <span className="text-sm text-muted">{h.desc}</span>
            </li>
          ))}
        </ul>
      </>
    ),
  },
  "watch.threshold": {
    cmd: "/watch",
    arg: "u7X2 threshold 250",
    output: (
      <>
        <StatusLine icon={Check}>Threshold set</StatusLine>
        <Product />
        <div className="mt-2 flex items-end gap-3">
          <span className="tnum text-2xl font-semibold text-cyan">$250.00</span>
          <span className="mb-1 font-mono text-[0.65rem] uppercase tracking-[0.14em] text-faint">
            target price
          </span>
        </div>
        <p className="mt-3 text-sm text-muted">
          Pings the channel when it drops to{" "}
          <span className="text-fg">$250.00</span> or below.
        </p>
        <div className="mt-4 grid grid-cols-2 gap-px border border-line bg-line">
          <Cell label="Watch ID" value="u7X2B3C" />
          <Cell label="Was" value="any drop" />
          <Cell label="Alerts" value="drop · threshold · restock" accent />
          <Cell label="Status" value="active" />
        </div>
      </>
    ),
  },
  "watch.alert": {
    cmd: "/watch",
    arg: "u7X2 alert add threshold",
    output: (
      <>
        <StatusLine icon={BellPlus}>Rule added</StatusLine>
        <p className="mt-3 text-sm text-muted">
          Threshold alerts are now <span className="text-fg">on</span> for this
          watch.
        </p>
        <div className="mt-4 grid grid-cols-2 gap-px border border-line bg-line">
          <Cell label="Subscribed" value="drop · threshold · restock" accent />
          <Cell label="Watch ID" value="u7X2B3C" />
          <Cell label="Product" value="Sony WH-1000XM5" />
          <Cell label="Status" value="active" />
        </div>
      </>
    ),
  },
  "watch.pause": {
    cmd: "/watch",
    arg: "u7X2 pause",
    output: (
      <>
        <StatusLine icon={Pause}>Watch paused</StatusLine>
        <p className="mt-3 text-sm text-muted">
          Scraping and alerts are paused. Nothing fires until you resume.
        </p>
        <div className="mt-4 grid grid-cols-2 gap-px border border-line bg-line">
          <Cell label="Watch ID" value="u7X2B3C" />
          <Cell label="Product" value="Sony WH-1000XM5" />
          <Cell label="State" value="paused" />
          <Cell label="Resume" value="/watch u7X2 resume" accent />
        </div>
      </>
    ),
  },
  "watch.refresh": {
    cmd: "/watch",
    arg: "u7X2 refresh",
    output: (
      <>
        <StatusLine icon={RefreshCw}>Rechecked now</StatusLine>
        <Product />
        <div className="mt-2 flex items-end gap-3">
          <span className="tnum text-2xl font-semibold text-cyan">$341.50</span>
          <span className="mb-1 font-mono text-[0.65rem] uppercase tracking-[0.14em] text-faint">
            checked just now
          </span>
        </div>
        <div className="mt-4 grid grid-cols-2 gap-px border border-line bg-line">
          <Cell label="Was" value="$349.99" />
          <Cell label="Now" value="$341.50" accent />
          <Cell label="Scrape tier" value="adapter" />
          <Cell label="Stock" value="in stock" />
        </div>
      </>
    ),
  },
  "watch.channel": {
    cmd: "/watch",
    arg: "u7X2 channel #price-drops",
    output: (
      <>
        <StatusLine icon={Hash}>Alerts rerouted</StatusLine>
        <p className="mt-3 text-sm text-muted">
          This watch now posts to{" "}
          <span className="text-fg">#price-drops</span>, not the server default.
        </p>
        <div className="mt-4 grid grid-cols-2 gap-px border border-line bg-line">
          <Cell label="Watch ID" value="u7X2B3C" />
          <Cell label="Channel" value="#price-drops" accent />
          <Cell label="Scope" value="this watch only" />
          <Cell label="Status" value="active" />
        </div>
      </>
    ),
  },
  "watch.role": {
    cmd: "/watch",
    arg: "u7X2 role @deal-hunters",
    output: (
      <>
        <StatusLine icon={AtSign}>Mention set</StatusLine>
        <p className="mt-3 text-sm text-muted">
          Pings <span className="text-fg">@deal-hunters</span> whenever this
          watch fires.
        </p>
        <div className="mt-4 grid grid-cols-2 gap-px border border-line bg-line">
          <Cell label="Watch ID" value="u7X2B3C" />
          <Cell label="Mention" value="@deal-hunters" accent />
          <Cell label="Scope" value="this watch only" />
          <Cell label="Status" value="active" />
        </div>
      </>
    ),
  },
};

const TOP: { key: string; index: string; name: string; tagline: string; icon: IconType }[] = [
  { key: "track", index: "01", name: "Track", tagline: "Start a watch", icon: Crosshair },
  { key: "config", index: "02", name: "Config", tagline: "Set up the server", icon: Settings2 },
  { key: "help", index: "03", name: "Help", tagline: "Every command", icon: Terminal },
];

const WATCH_SUBS: { key: string; name: string; desc: string }[] = [
  { key: "watch.threshold", name: "threshold", desc: "set a target price" },
  { key: "watch.alert", name: "alert", desc: "toggle a rule" },
  { key: "watch.pause", name: "pause", desc: "pause + resume" },
  { key: "watch.refresh", name: "refresh", desc: "scrape now" },
  { key: "watch.channel", name: "channel", desc: "reroute alerts" },
  { key: "watch.role", name: "role", desc: "set a mention" },
];

export function HowItWorks() {
  const [active, setActive] = useState<string>("track");
  const current = DATA[active];
  const watchOpen = active.startsWith("watch.");

  return (
    <section id="how" className="relative scroll-mt-20 px-5 py-24">
      <div className="mx-auto max-w-6xl">
        <Reveal className="max-w-2xl">
          <p className="eyebrow">[ how it works ]</p>
          <h2 className="mt-4 font-pixel text-[clamp(1.4rem,3.5vw,2.4rem)] leading-tight">
            Run it, see it
          </h2>
          <p className="mt-4 text-muted">
            No docs to read. Pick a module and watch the exact command, and
            exactly what the bot replies.
          </p>
        </Reveal>

        <Reveal delay={100} className="mt-12">
          <div className="panel">
            <div className="flex items-center justify-between border-b border-line px-4 py-3">
              <span className="font-mono text-xs uppercase tracking-[0.16em] text-faint">
                price-tracker // console
              </span>
              <span className="font-mono text-xs text-faint">4 modules</span>
            </div>

            <div className="grid gap-px bg-line lg:grid-cols-[17rem_1fr]">
              {/* module rail */}
              <div
                role="tablist"
                aria-label="Command modules"
                className="flex flex-row overflow-x-auto bg-ink-1 lg:flex-col lg:overflow-visible"
              >
                {TOP.map((cog) => {
                  const on = cog.key === active;
                  return (
                    <button
                      key={cog.key}
                      role="tab"
                      aria-selected={on}
                      onClick={() => setActive(cog.key)}
                      className={cn(
                        "flex shrink-0 items-center gap-3 border-b border-line px-5 py-4 text-left transition-colors duration-150 lg:w-full",
                        on ? "bg-ink-2" : "hover:bg-ink-2/50",
                      )}
                    >
                      <span className={cn("tnum text-sm font-semibold", on ? "text-cyan" : "text-faint")}>
                        {cog.index}
                      </span>
                      <cog.icon className={cn("h-4 w-4 shrink-0", on ? "text-cyan" : "text-muted")} />
                      <span className="flex flex-col">
                        <span className={cn("font-mono text-xs uppercase tracking-[0.14em]", on ? "text-fg" : "text-muted")}>
                          {cog.name}
                        </span>
                        <span className="hidden text-[0.7rem] text-faint lg:block">
                          {cog.tagline}
                        </span>
                      </span>
                      {on && <span className="ml-auto hidden h-2 w-2 bg-cyan lg:block" />}
                    </button>
                  );
                })}

                {/* watch group header */}
                <button
                  role="tab"
                  aria-selected={watchOpen}
                  onClick={() => setActive("watch.threshold")}
                  className={cn(
                    "flex shrink-0 items-center gap-3 border-b border-line px-5 py-4 text-left transition-colors duration-150 lg:w-full",
                    watchOpen ? "bg-ink-2" : "hover:bg-ink-2/50",
                  )}
                >
                  <span className={cn("tnum text-sm font-semibold", watchOpen ? "text-cyan" : "text-faint")}>
                    04
                  </span>
                  <Eye className={cn("h-4 w-4 shrink-0", watchOpen ? "text-cyan" : "text-muted")} />
                  <span className="flex flex-col">
                    <span className={cn("font-mono text-xs uppercase tracking-[0.14em]", watchOpen ? "text-fg" : "text-muted")}>
                      Watch
                    </span>
                    <span className="hidden text-[0.7rem] text-faint lg:block">
                      Tune a watch
                    </span>
                  </span>
                  <span className="ml-auto hidden font-mono text-[0.6rem] text-faint lg:block">
                    {WATCH_SUBS.length}
                  </span>
                </button>

                {/* watch subcommands */}
                <div className="flex flex-row bg-ink-1 lg:flex-col">
                  {WATCH_SUBS.map((sub) => {
                    const on = sub.key === active;
                    return (
                      <button
                        key={sub.key}
                        role="tab"
                        aria-selected={on}
                        onClick={() => setActive(sub.key)}
                        className={cn(
                          "flex shrink-0 items-center gap-2.5 border-b border-line px-5 py-3 text-left transition-colors duration-150 lg:w-full lg:pl-12",
                          on ? "bg-ink-2" : "hover:bg-ink-2/50",
                        )}
                      >
                        <span className={cn("hidden h-px w-3 shrink-0 lg:block", on ? "bg-cyan" : "bg-line-strong")} />
                        <span className={cn("font-mono text-[0.72rem] uppercase tracking-[0.12em]", on ? "text-cyan" : "text-muted")}>
                          {sub.name}
                        </span>
                        <span className="hidden text-[0.66rem] text-faint lg:block">
                          {sub.desc}
                        </span>
                        {on && <span className="ml-auto hidden h-1.5 w-1.5 bg-cyan lg:block" />}
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* command + output pane */}
              <div className="bg-ink-1 p-5 sm:p-7">
                <div className="flex items-center gap-2 border border-line bg-ink px-4 py-3 font-mono text-sm">
                  <span className="text-faint">$</span>
                  <span className="text-cyan">{current.cmd}</span>
                  {current.arg && <span className="truncate text-muted">{current.arg}</span>}
                  <span className="caret ml-0.5" aria-hidden />
                  <span className="ml-auto hidden shrink-0 border border-cyan/50 px-2 py-0.5 text-[0.6rem] uppercase tracking-[0.14em] text-cyan sm:block">
                    enter
                  </span>
                </div>

                <div className="mt-4 border border-line bg-ink">
                  <div className="flex items-center gap-2 border-b border-line px-4 py-2.5">
                    <span className="grid h-6 w-6 place-items-center border border-line">
                      <TrackerMark className="h-3.5 w-3.5" />
                    </span>
                    <span className="text-xs font-semibold text-fg">Price Tracker</span>
                    <span className="border border-line px-1.5 py-0.5 font-mono text-[0.55rem] uppercase tracking-wide text-faint">
                      App
                    </span>
                    <span className="ml-auto font-mono text-[0.62rem] uppercase tracking-wide text-faint">
                      only you can see this
                    </span>
                  </div>
                  <div className="p-5">{current.output}</div>
                </div>
              </div>
            </div>
          </div>
        </Reveal>
      </div>
    </section>
  );
}
