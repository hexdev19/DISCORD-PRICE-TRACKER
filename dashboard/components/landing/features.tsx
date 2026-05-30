import {
  Boxes,
  BellRing,
  LineChart,
  PackageCheck,
  SlidersHorizontal,
  Globe,
  Link2,
  ArrowRight,
} from "lucide-react";
import { Reveal } from "./reveal";

const SMALL = [
  {
    icon: BellRing,
    title: "Alerts that land where they should",
    body: "Route each watch to a channel and ping the right role. Threshold, target price, or any drop. No noise.",
  },
  {
    icon: LineChart,
    title: "Price history on every watch",
    body: "Every tracked product keeps a full price timeline, so you know whether a deal is actually a deal.",
  },
  {
    icon: PackageCheck,
    title: "Back-in-stock alerts",
    body: "Sold out? Price Tracker keeps watching and pings the moment inventory returns.",
  },
  {
    icon: SlidersHorizontal,
    title: "Rules per watch",
    body: "Target price, percent drop, region override, mute windows. Tune each product on its own terms.",
  },
  {
    icon: Globe,
    title: "Native currency and regions",
    body: "Prices stay in their real currency and convert on display, with per-server region defaults.",
  },
];

function ExtractionFlow() {
  return (
    <div className="mt-7 border border-line bg-ink p-4">
      <div className="flex items-center gap-3">
        <span className="flex min-w-0 flex-1 items-center gap-2 border border-line bg-ink-2 px-3 py-2.5">
          <Link2 className="h-4 w-4 shrink-0 text-faint" />
          <span className="tnum truncate text-xs text-muted">
            amazon.com/dp/B0C33XXL
          </span>
        </span>
        <ArrowRight className="h-4 w-4 shrink-0 text-faint" />
        <span className="flex shrink-0 items-center border border-cyan bg-cyan/10 px-3 py-2.5">
          <span className="tnum text-sm font-semibold text-cyan">$278.00</span>
        </span>
      </div>
      <p className="mt-3 font-mono text-[0.7rem] leading-relaxed text-faint">
        Structured data, per-site adapters, then a stealth browser when a site
        fights back. Every tier, so a link is all you give it.
      </p>
    </div>
  );
}

export function Features() {
  return (
    <section id="features" className="relative scroll-mt-20 px-5 py-24">
      <div className="mx-auto max-w-6xl">
        <Reveal className="max-w-2xl">
          <p className="eyebrow">[ features ]</p>
          <h2 className="mt-4 font-pixel text-[clamp(1.4rem,3.5vw,2.4rem)] leading-tight">
            Deal toolkit
          </h2>
          <p className="mt-4 text-muted">
            Everything your server needs to never overpay again.
          </p>
        </Reveal>

        <div className="mt-12 grid gap-px border border-line bg-line lg:grid-cols-6">
          {/* Big tile */}
          <Reveal className="lg:col-span-3 lg:row-span-2">
            <div className="lift flex h-full flex-col bg-ink-1 p-7">
              <span className="grid h-11 w-11 place-items-center border border-line text-cyan">
                <Boxes className="h-5 w-5" />
              </span>
              <h3 className="mt-5 text-2xl font-semibold">
                Drop a link from anywhere
              </h3>
              <p className="mt-3 max-w-md text-muted">
                Amazon, eBay, AliExpress, Walmart, Best Buy, Target and most
                stores in between. Paste a URL and Price Tracker resolves the
                price, even on sites that try to hide it.
              </p>
              <ExtractionFlow />
              <div className="mt-auto flex flex-wrap gap-2 pt-6">
                {["Amazon", "eBay", "Walmart", "AliExpress", "Best Buy", "Target"].map(
                  (s) => (
                    <span
                      key={s}
                      className="border border-line px-3 py-1 font-mono text-[0.7rem] uppercase tracking-wide text-muted"
                    >
                      {s}
                    </span>
                  ),
                )}
              </div>
            </div>
          </Reveal>

          {/* Small tiles */}
          {SMALL.map((f, i) => (
            <Reveal
              key={f.title}
              delay={i * 50}
              className={i < 2 ? "lg:col-span-3" : "lg:col-span-2"}
            >
              <div className="lift flex h-full flex-col bg-ink-1 p-6">
                <span className="grid h-10 w-10 place-items-center border border-line text-cyan">
                  <f.icon className="h-[1.1rem] w-[1.1rem]" />
                </span>
                <h3 className="mt-4 text-lg font-semibold">{f.title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-muted">
                  {f.body}
                </p>
              </div>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}
