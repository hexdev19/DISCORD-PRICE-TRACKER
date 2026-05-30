import Link from "next/link";
import { ChevronLeft } from "lucide-react";

export function PageHeader({
  eyebrow,
  title,
  back,
  children,
}: {
  eyebrow: string;
  title: string;
  back?: { href: string; label: string };
  children?: React.ReactNode;
}) {
  return (
    <div className="mb-8 flex flex-col gap-4 border-b border-line pb-6 sm:flex-row sm:items-end sm:justify-between">
      <div className="min-w-0">
        {back && (
          <Link
            href={back.href}
            className="mb-3 inline-flex items-center gap-1 font-mono text-[0.7rem] uppercase tracking-[0.16em] text-faint transition-colors hover:text-cyan"
          >
            <ChevronLeft className="h-3.5 w-3.5" />
            {back.label}
          </Link>
        )}
        <p className="eyebrow">{eyebrow}</p>
        <h1 className="mt-2 truncate text-2xl sm:text-3xl">{title}</h1>
      </div>
      {children && <div className="flex flex-wrap items-center gap-3">{children}</div>}
    </div>
  );
}

export function StockPill({ inStock }: { inStock: boolean | null }) {
  const label =
    inStock === null ? "Unknown" : inStock ? "In stock" : "Out of stock";
  const tone =
    inStock === null
      ? "border-line text-faint"
      : inStock
        ? "border-cyan text-cyan"
        : "border-line-strong text-muted";
  return (
    <span
      className={`inline-flex items-center gap-1.5 border px-2 py-0.5 font-mono text-[0.65rem] uppercase tracking-[0.12em] ${tone}`}
    >
      {inStock !== null && (
        <span
          className={`h-1.5 w-1.5 ${inStock ? "bg-cyan" : "bg-faint"}`}
          aria-hidden
        />
      )}
      {label}
    </span>
  );
}

export function StatusPill({
  isActive,
  paused,
}: {
  isActive: boolean;
  paused: boolean;
}) {
  const label = !isActive ? "Inactive" : paused ? "Paused" : "Active";
  const tone =
    !isActive || paused
      ? "border-line-strong text-muted"
      : "border-cyan text-cyan";
  return (
    <span
      className={`inline-flex items-center border px-2 py-0.5 font-mono text-[0.65rem] uppercase tracking-[0.12em] ${tone}`}
    >
      {label}
    </span>
  );
}

export function AdminBadge({ isAdmin }: { isAdmin: boolean }) {
  if (!isAdmin) return null;
  return (
    <span className="inline-flex items-center border border-line-strong px-2 py-0.5 font-mono text-[0.6rem] uppercase tracking-[0.14em] text-faint">
      Admin
    </span>
  );
}

export function formatPrice(
  price: number | null,
  currency: string | null,
): string {
  if (price === null) return "—";
  try {
    return new Intl.NumberFormat(undefined, {
      style: "currency",
      currency: currency ?? "USD",
      currencyDisplay: "narrowSymbol",
    }).format(price);
  } catch {
    return `${price.toFixed(2)}${currency ? ` ${currency}` : ""}`;
  }
}

export function formatDate(iso: string | null): string {
  if (!iso) return "Never";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "—";
  return d.toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}
