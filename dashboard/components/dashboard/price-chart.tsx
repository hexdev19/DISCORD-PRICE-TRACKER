"use client";

import { useMemo } from "react";
import type { SnapshotPoint } from "@/lib/api";
import { formatPrice } from "./page-header";

const W = 720;
const H = 240;
const PAD = { top: 16, right: 16, bottom: 28, left: 56 };

type P = { x: number; y: number; price: number; t: string };

export function PriceChart({
  points,
  currency,
}: {
  points: SnapshotPoint[];
  currency: string | null;
}) {
  const priced = useMemo(
    () =>
      points
        .filter((p): p is SnapshotPoint & { price: number } => p.price !== null)
        .map((p) => ({ t: new Date(p.t).getTime(), price: p.price })),
    [points],
  );

  if (priced.length < 2) {
    return (
      <div className="panel-quiet grid h-[240px] place-items-center p-6 text-center">
        <p className="text-balance text-sm text-muted">
          Not enough price history in this range yet. Check back once the watch
          has recorded a few snapshots.
        </p>
      </div>
    );
  }

  const ts = priced.map((p) => p.t);
  const prices = priced.map((p) => p.price);
  const minT = Math.min(...ts);
  const maxT = Math.max(...ts);
  const minP = Math.min(...prices);
  const maxP = Math.max(...prices);
  const spanT = maxT - minT || 1;
  const spanP = maxP - minP || maxP || 1;

  const innerW = W - PAD.left - PAD.right;
  const innerH = H - PAD.top - PAD.bottom;

  const sx = (t: number) => PAD.left + ((t - minT) / spanT) * innerW;
  const sy = (p: number) =>
    PAD.top + innerH - ((p - minP) / spanP) * innerH;

  const coords: P[] = priced.map((p) => ({
    x: sx(p.t),
    y: sy(p.price),
    price: p.price,
    t: new Date(p.t).toISOString(),
  }));

  const line = coords.map((c) => `${c.x},${c.y}`).join(" ");
  const area = `${PAD.left},${PAD.top + innerH} ${line} ${
    PAD.left + innerW
  },${PAD.top + innerH}`;

  const lowIdx = prices.indexOf(minP);
  const low = coords[lowIdx];

  const ticks = [maxP, (maxP + minP) / 2, minP];

  return (
    <div className="panel p-4">
      <svg
        viewBox={`0 0 ${W} ${H}`}
        className="h-auto w-full"
        role="img"
        aria-label="Price history"
        preserveAspectRatio="xMidYMid meet"
      >
        {ticks.map((p, i) => {
          const y = sy(p);
          return (
            <g key={i}>
              <line
                x1={PAD.left}
                y1={y}
                x2={W - PAD.right}
                y2={y}
                stroke="var(--color-line)"
                strokeWidth="1"
              />
              <text
                x={PAD.left - 8}
                y={y + 3}
                textAnchor="end"
                className="tnum"
                fill="var(--color-faint)"
                fontSize="10"
              >
                {formatPrice(p, currency)}
              </text>
            </g>
          );
        })}

        <polyline
          points={area}
          fill="var(--color-cyan)"
          fillOpacity="0.07"
          stroke="none"
        />
        <polyline
          points={line}
          fill="none"
          stroke="var(--color-cyan)"
          strokeWidth="2"
          strokeLinejoin="round"
          strokeLinecap="round"
        />

        <line
          x1={low.x}
          y1={PAD.top}
          x2={low.x}
          y2={PAD.top + innerH}
          stroke="var(--color-cyan-dim)"
          strokeWidth="1"
          strokeDasharray="3 4"
        />
        <rect
          x={low.x - 3}
          y={low.y - 3}
          width="6"
          height="6"
          fill="var(--color-cyan-bright)"
        />
        <text
          x={Math.min(Math.max(low.x, PAD.left + 40), W - PAD.right - 40)}
          y={PAD.top + innerH + 20}
          textAnchor="middle"
          className="tnum"
          fill="var(--color-cyan)"
          fontSize="10"
        >
          low {formatPrice(minP, currency)}
        </text>
      </svg>
    </div>
  );
}
