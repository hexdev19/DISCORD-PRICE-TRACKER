import { cn } from "@/lib/utils";

/**
 * Price Tracker mark: a hard square containing a downward step (a price
 * falling through a tracked range). Sharp, flat, single cyan stroke.
 */
export function TrackerMark({ className }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      className={cn("h-6 w-6", className)}
      aria-hidden
    >
      <rect
        x="1.5"
        y="1.5"
        width="21"
        height="21"
        stroke="var(--color-cyan)"
        strokeWidth="1.5"
      />
      <path
        d="M5 7h4v4h4v4h6"
        stroke="var(--color-cyan)"
        strokeWidth="1.5"
      />
      <path
        d="M19 15v-3m0 3h-3"
        stroke="var(--color-cyan)"
        strokeWidth="1.5"
        strokeLinecap="square"
      />
    </svg>
  );
}

export function Wordmark({ className }: { className?: string }) {
  return (
    <span
      className={cn(
        "font-pixel text-[0.8rem] uppercase tracking-[0.08em] text-fg",
        className,
      )}
    >
      Price&nbsp;Tracker
    </span>
  );
}
