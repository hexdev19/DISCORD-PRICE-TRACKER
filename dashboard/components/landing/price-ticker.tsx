import { ArrowDown, Box } from "lucide-react";

type Tick =
  | { kind: "drop"; name: string; pct: string; price: string }
  | { kind: "stock"; name: string; price: string };

const TICKS: Tick[] = [
  { kind: "drop", name: "RTX 4080 Super", pct: "-18%", price: "$799" },
  { kind: "stock", name: "PS5 Slim Bundle", price: "$449" },
  { kind: "drop", name: "AirPods Pro 2", pct: "-24%", price: "$189" },
  { kind: "drop", name: 'LG C4 65"', pct: "-31%", price: "$1,296" },
  { kind: "stock", name: "Steam Deck OLED", price: "$549" },
  { kind: "drop", name: "Kindle Paperwhite", pct: "-22%", price: "$109" },
  { kind: "drop", name: "Dyson V15 Detect", pct: "-15%", price: "$549" },
  { kind: "stock", name: "Meta Quest 3", price: "$499" },
  { kind: "drop", name: "Nintendo Switch 2", pct: "-12%", price: "$399" },
  { kind: "drop", name: "Bose QC Ultra", pct: "-27%", price: "$309" },
];

function TickItem({ tick }: { tick: Tick }) {
  return (
    <span className="flex items-center gap-2.5 whitespace-nowrap border-r border-line px-6 py-3.5">
      {tick.kind === "drop" ? (
        <ArrowDown className="h-3.5 w-3.5 text-cyan" />
      ) : (
        <Box className="h-3.5 w-3.5 text-cyan" />
      )}
      <span className="font-mono text-xs text-muted">{tick.name}</span>
      {tick.kind === "drop" ? (
        <span className="tnum text-xs font-semibold text-cyan">{tick.pct}</span>
      ) : (
        <span className="font-mono text-[0.65rem] uppercase tracking-wide text-cyan">
          restock
        </span>
      )}
      <span className="tnum text-xs text-faint">{tick.price}</span>
    </span>
  );
}

export function PriceTicker() {
  const row = [...TICKS, ...TICKS];
  return (
    <section
      className="marquee-track overflow-hidden border-y border-line bg-ink-1"
      aria-label="Recent price drops and restocks"
    >
      <div className="marquee">
        {row.map((tick, i) => (
          <TickItem key={i} tick={tick} />
        ))}
      </div>
    </section>
  );
}
