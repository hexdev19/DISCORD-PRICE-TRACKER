"use client";

import { useEffect, useRef, useState } from "react";

type CountUpProps = {
  to: number;
  /** Suffix like "K", "M", "+". */
  suffix?: string;
  prefix?: string;
  decimals?: number;
  durationMs?: number;
};

const easeOutExpo = (t: number): number =>
  t === 1 ? 1 : 1 - Math.pow(2, -10 * t);

/** Counts from 0 to `to` once it scrolls into view. */
export function CountUp({
  to,
  suffix = "",
  prefix = "",
  decimals = 0,
  durationMs = 1600,
}: CountUpProps) {
  const ref = useRef<HTMLSpanElement>(null);
  const [value, setValue] = useState(0);
  const started = useRef(false);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;

    const reduce = window.matchMedia(
      "(prefers-reduced-motion: reduce)",
    ).matches;
    if (reduce) {
      setValue(to);
      return;
    }

    const io = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (!entry.isIntersecting || started.current) continue;
          started.current = true;
          const start = performance.now();
          const tick = (now: number) => {
            const t = Math.min((now - start) / durationMs, 1);
            setValue(to * easeOutExpo(t));
            if (t < 1) requestAnimationFrame(tick);
          };
          requestAnimationFrame(tick);
        }
      },
      { threshold: 0.4 },
    );

    io.observe(el);
    return () => io.disconnect();
  }, [to, durationMs]);

  return (
    <span ref={ref} className="tnum">
      {prefix}
      {value.toLocaleString("en-US", {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals,
      })}
      {suffix}
    </span>
  );
}
