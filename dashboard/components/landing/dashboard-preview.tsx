import { ArrowDown, ArrowUp } from "lucide-react";
import { Reveal } from "./reveal";
import { GhostButton } from "./buttons";
import { loginUrl } from "@/lib/api";

/**
 * Price-history chart: flat cyan line, gray out-of-stock bands, a
 * lowest-in-range marker. No fills/glows beyond a faint area tint.
 */
function PriceHistoryChart() {
  return (
    <svg
      viewBox="0 0 600 240"
      className="h-full w-full"
      role="img"
      aria-label="Price history for Sony WH-1000XM5 over 90 days"
    >
      {[40, 90, 140, 190].map((y) => (
        <line key={y} x1="0" x2="600" y1={y} y2={y} stroke="oklch(1 0 0 / 0.06)" strokeWidth="1" />
      ))}

      {/* out-of-stock bands */}
      <rect x="150" y="0" width="70" height="210" fill="oklch(0.6 0.01 240 / 0.12)" />
      <rect x="430" y="0" width="40" height="210" fill="oklch(0.6 0.01 240 / 0.12)" />

      <polyline
        points="0,210 0,70 70,76 150,64 220,96 300,120 380,150 430,176 470,168 540,184 600,182 600,210"
        fill="oklch(0.8 0.13 215 / 0.08)"
        stroke="none"
      />
      <polyline
        points="0,70 70,76 150,64 220,96 300,120 380,150 430,176 470,168 540,184 600,182"
        fill="none"
        stroke="oklch(0.8 0.13 215)"
        strokeWidth="2"
        strokeLinejoin="miter"
      />

      {/* lowest-in-range marker */}
      <line x1="540" y1="184" x2="540" y2="210" stroke="oklch(0.8 0.13 215 / 0.5)" strokeDasharray="3 3" />
      <rect x="535" y="179" width="10" height="10" fill="oklch(0.165 0.005 240)" stroke="oklch(0.8 0.13 215)" strokeWidth="2" />
      <g transform="translate(452,150)">
        <rect width="92" height="24" fill="oklch(0.235 0.007 240)" stroke="oklch(0.8 0.13 215 / 0.5)" />
        <text x="10" y="16" fontSize="12" fill="oklch(0.87 0.12 210)" fontFamily="var(--font-mono)">
          Lowest $278
        </text>
      </g>
    </svg>
  );
}

const WATCHES = [
  { name: "Sony WH-1000XM5", store: "Amazon", price: "$278.00", change: "-30%", down: true },
  { name: "RTX 4080 Super", store: "Best Buy", price: "$799.00", change: "-18%", down: true },
  { name: 'LG C4 OLED 65"', store: "Walmart", price: "$1,296", change: "-31%", down: true },
  { name: "Steam Deck OLED", store: "Steam", price: "$549.00", change: "+0%", down: false },
];

export function DashboardPreview() {
  return (
    <section id="dashboard" className="relative scroll-mt-20 px-5 py-24">
      <div className="mx-auto max-w-6xl">
        <Reveal className="max-w-2xl">
          <p className="eyebrow">[ dashboard ]</p>
          <h2 className="mt-4 font-pixel text-[clamp(1.4rem,3.5vw,2.4rem)] leading-tight">
            The dashboard
          </h2>
          <p className="mt-4 max-w-xl text-muted">
            Sign in with Discord to see every watch, every alert, and the price
            history behind it. Read-only by design: the bot does the tracking,
            the dashboard shows you the receipts.
          </p>
          <div className="mt-7">
            <GhostButton href={loginUrl}>Open the dashboard</GhostButton>
          </div>
        </Reveal>

        <Reveal delay={100} className="mt-12">
          <div className="panel">
            {/* window bar */}
            <div className="flex items-center gap-2 border-b border-line px-4 py-3">
              <span className="flex gap-1.5">
                <span className="h-2.5 w-2.5 border border-line-strong" />
                <span className="h-2.5 w-2.5 border border-line-strong" />
                <span className="h-2.5 w-2.5 border border-line-strong" />
              </span>
              <span className="tnum mx-auto border border-line bg-ink px-3 py-1 text-xs text-faint">
                pricetracker.bot/dashboard/deal-hunters-hq
              </span>
            </div>

            {/* app chrome */}
            <div className="border-b border-line px-5 py-3.5">
              <div className="flex flex-wrap items-center gap-x-6 gap-y-2">
                <span className="font-mono text-sm font-semibold text-fg">
                  deal-hunters HQ
                </span>
                <div className="flex items-center gap-1 font-mono text-xs uppercase tracking-wide">
                  {["Overview", "Watches", "Alerts", "Config"].map((t, i) => (
                    <span
                      key={t}
                      className={
                        i === 0
                          ? "border border-line bg-ink-2 px-3 py-1 text-cyan"
                          : "px-3 py-1 text-faint"
                      }
                    >
                      {t}
                    </span>
                  ))}
                </div>
              </div>
            </div>

            {/* body */}
            <div className="grid gap-px bg-line p-px lg:grid-cols-3">
              {/* chart card */}
              <div className="bg-ink-1 p-5 lg:col-span-2">
                <div className="flex items-start justify-between">
                  <div>
                    <p className="text-sm font-medium text-fg">Sony WH-1000XM5</p>
                    <p className="tnum text-xs text-faint">
                      90-day price history · Amazon
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="tnum text-xl font-semibold text-cyan">$278.00</p>
                    <p className="tnum flex items-center justify-end gap-1 text-xs text-cyan">
                      <ArrowDown className="h-3 w-3" /> 30% in 90d
                    </p>
                  </div>
                </div>
                <div className="mt-3 h-44">
                  <PriceHistoryChart />
                </div>
                <div className="mt-2 flex items-center gap-4 font-mono text-[0.65rem] uppercase tracking-wide text-faint">
                  <span className="flex items-center gap-1.5">
                    <span className="h-2 w-3 bg-[oklch(0.6_0.01_240/0.3)]" />
                    out of stock
                  </span>
                  <span className="flex items-center gap-1.5">
                    <span className="h-0.5 w-3 bg-cyan" />
                    price
                  </span>
                </div>
              </div>

              {/* stat column */}
              <div className="grid grid-rows-2 gap-px bg-line">
                <div className="bg-ink-1 p-5">
                  <p className="font-mono text-xs uppercase tracking-wide text-faint">
                    Active watches
                  </p>
                  <p className="tnum mt-1 text-2xl font-semibold text-fg">48</p>
                  <p className="tnum mt-1 flex items-center gap-1 text-xs text-cyan">
                    <ArrowUp className="h-3 w-3" /> 6 this week
                  </p>
                </div>
                <div className="bg-ink-1 p-5">
                  <p className="font-mono text-xs uppercase tracking-wide text-faint">
                    Alerts this week
                  </p>
                  <p className="tnum mt-1 text-2xl font-semibold text-fg">23</p>
                  <p className="tnum mt-1 text-xs text-muted">avg drop 19%</p>
                </div>
              </div>

              {/* watch table */}
              <div className="bg-ink-1 lg:col-span-3">
                <div className="hidden grid-cols-[2fr_1fr_1fr_0.7fr] gap-4 border-b border-line px-5 py-2.5 font-mono text-[0.65rem] uppercase tracking-wide text-faint sm:grid">
                  <span>Product</span>
                  <span>Store</span>
                  <span>Price</span>
                  <span className="text-right">90d</span>
                </div>
                {WATCHES.map((w) => (
                  <div
                    key={w.name}
                    className="grid grid-cols-2 gap-4 border-b border-line px-5 py-3 text-sm last:border-0 sm:grid-cols-[2fr_1fr_1fr_0.7fr]"
                  >
                    <span className="font-medium text-fg">{w.name}</span>
                    <span className="font-mono text-xs text-faint">{w.store}</span>
                    <span className="tnum text-muted">{w.price}</span>
                    <span
                      className={`tnum text-right font-semibold ${
                        w.down ? "text-cyan" : "text-faint"
                      }`}
                    >
                      {w.change}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </Reveal>
      </div>
    </section>
  );
}
