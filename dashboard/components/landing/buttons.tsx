import Link from "next/link";
import { ArrowRight } from "lucide-react";
import { cn } from "@/lib/utils";

const base =
  "group inline-flex items-center justify-center gap-2 border font-mono text-xs font-semibold uppercase tracking-[0.12em] transition-colors duration-200 focus-visible:outline-2";

type Props = {
  href: string;
  children: React.ReactNode;
  className?: string;
  size?: "md" | "lg";
};

/** Solid cyan, sharp corners. Inverts to outline on hover. */
export function PrimaryButton({ href, children, className, size = "md" }: Props) {
  return (
    <Link
      href={href}
      className={cn(
        base,
        size === "lg" ? "px-6 py-3.5" : "px-4 py-2.5",
        "border-cyan bg-cyan text-ink hover:bg-transparent hover:text-cyan",
        className,
      )}
    >
      {children}
      <ArrowRight className="h-3.5 w-3.5 transition-transform duration-200 group-hover:translate-x-0.5" />
    </Link>
  );
}

/** Hairline outline. Border + text go cyan on hover. */
export function GhostButton({ href, children, className, size = "md" }: Props) {
  return (
    <Link
      href={href}
      className={cn(
        base,
        size === "lg" ? "px-6 py-3.5" : "px-4 py-2.5",
        "border-line-strong text-fg hover:border-cyan hover:text-cyan",
        className,
      )}
    >
      {children}
    </Link>
  );
}
