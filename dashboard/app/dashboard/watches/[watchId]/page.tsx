"use client";

import Image from "next/image";
import { use, useMemo, useState } from "react";
import { ExternalLink, ImageOff } from "lucide-react";
import {
  getSnapshots,
  getWatch,
  type AlertRow,
  type AlertRules,
} from "@/lib/api";
import { useAsync } from "@/lib/use-async";
import {
  EmptyState,
  ErrorPanel,
  Skeleton,
  Spinner,
} from "@/components/dashboard/states";
import {
  formatDate,
  formatPrice,
  PageHeader,
  StatusPill,
  StockPill,
} from "@/components/dashboard/page-header";
import { PriceChart } from "@/components/dashboard/price-chart";
import { cn } from "@/lib/utils";

const RANGES = [
  { label: "7d", days: 7 },
  { label: "30d", days: 30 },
  { label: "90d", days: 90 },
] as const;

export default function WatchPage({
  params,
}: {
  params: Promise<{ watchId: string }>;
}) {
  const { watchId } = use(params);
  const [days, setDays] = useState(30);
  const watch = useAsync(() => getWatch(watchId), [watchId]);

  const range = useMemo(() => {
    const to = new Date();
    const from = new Date(to.getTime() - days * 86_400_000);
    return { from: from.toISOString(), to: to.toISOString() };
  }, [days]);

  const snaps = useAsync(
    () => getSnapshots(watchId, range),
    [watchId, range.from, range.to],
  );

  if (watch.loading) {
    return (
      <>
        <Skeleton className="h-10 w-48" />
        <Skeleton className="mt-6 h-40 w-full" />
        <Skeleton className="mt-6 h-64 w-full" />
      </>
    );
  }
  if (watch.error || !watch.data) {
    return (
      <>
        <PageHeader
          eyebrow="Watch"
          title="Details"
          back={{ href: "/dashboard", label: "All servers" }}
        />
        <ErrorPanel error={watch.error} onRetry={watch.reload} />
      </>
    );
  }

  const { product, alertRules, alerts, isActive, paused } = watch.data;

  return (
    <>
      <PageHeader
        eyebrow={product.domain}
        title={product.title ?? "Untitled product"}
        back={{
          href: `/dashboard/servers/${watch.data.guildId}`,
          label: "Back to server",
        }}
      >
        <StatusPill isActive={isActive} paused={paused} />
      </PageHeader>

      <section className="panel mb-8 flex flex-col gap-6 p-6 sm:flex-row">
        <div className="grid h-32 w-32 shrink-0 place-items-center border border-line bg-ink-2">
          {product.imageUrl ? (
            <Image
              src={product.imageUrl}
              alt=""
              width={128}
              height={128}
              className="h-full w-full object-contain"
              unoptimized
            />
          ) : (
            <ImageOff className="h-8 w-8 text-faint" aria-hidden />
          )}
        </div>

        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-baseline gap-x-4 gap-y-1">
            <span className="tnum text-3xl text-fg">
              {formatPrice(product.lastPrice, product.currency)}
            </span>
            <StockPill inStock={product.inStock} />
          </div>

          <dl className="mt-5 grid grid-cols-2 gap-x-6 gap-y-3 text-sm sm:grid-cols-3">
            <Meta label="Brand" value={product.brand ?? "—"} />
            <Meta label="Domain" value={product.domain} />
            <Meta label="Last scraped" value={formatDate(product.lastScrapedAt)} />
            {product.lastScrapeStatus && (
              <Meta label="Scrape status" value={product.lastScrapeStatus} />
            )}
            <Meta label="Tracking since" value={formatDate(watch.data.createdAt)} />
          </dl>

          <a
            href={product.sourceUrl}
            target="_blank"
            rel="noreferrer noopener"
            className="mt-5 inline-flex items-center gap-2 border border-line-strong px-3 py-2 font-mono text-xs uppercase tracking-[0.12em] text-fg transition-colors hover:border-cyan hover:text-cyan"
          >
            View on {product.domain}
            <ExternalLink className="h-3.5 w-3.5" />
          </a>
        </div>
      </section>

      <section className="mb-8">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="eyebrow">Price history</h2>
          <div className="flex border border-line">
            {RANGES.map((r) => (
              <button
                key={r.label}
                type="button"
                onClick={() => setDays(r.days)}
                aria-pressed={days === r.days}
                className={cn(
                  "px-3 py-1.5 font-mono text-[0.7rem] uppercase tracking-[0.12em] transition-colors",
                  days === r.days
                    ? "bg-cyan text-ink"
                    : "text-muted hover:text-cyan",
                )}
              >
                {r.label}
              </button>
            ))}
          </div>
        </div>

        {snaps.loading ? (
          <div className="panel grid h-[240px] place-items-center">
            <Spinner label="Loading history" />
          </div>
        ) : snaps.error ? (
          <ErrorPanel error={snaps.error} onRetry={snaps.reload} />
        ) : (
          <PriceChart
            points={snaps.data?.points ?? []}
            currency={snaps.data?.currency ?? product.currency}
          />
        )}
      </section>

      <section className="mb-8">
        <h2 className="eyebrow mb-4">Alert rules</h2>
        <AlertRuleChips rules={alertRules} />
      </section>

      <section>
        <h2 className="eyebrow mb-4">Alert log</h2>
        <AlertLog alerts={alerts} currency={product.currency} />
      </section>
    </>
  );
}

function Meta({ label, value }: { label: string; value: string }) {
  return (
    <div className="min-w-0">
      <dt className="font-mono text-[0.65rem] uppercase tracking-[0.14em] text-faint">
        {label}
      </dt>
      <dd className="mt-0.5 truncate text-fg">{value}</dd>
    </div>
  );
}

function formatRuleValue(v: unknown): string {
  if (v === null || v === undefined) return "—";
  if (typeof v === "boolean") return v ? "on" : "off";
  return String(v);
}

function AlertRuleChips({ rules }: { rules: AlertRules }) {
  const entries = Object.entries(rules).filter(
    ([, v]) => v !== null && v !== undefined && v !== false,
  );
  if (entries.length === 0) {
    return <EmptyState title="No alert rules configured for this watch." />;
  }
  return (
    <div className="flex flex-wrap gap-2">
      {entries.map(([k, v]) => (
        <span
          key={k}
          className="inline-flex items-center gap-2 border border-line px-3 py-1.5 font-mono text-xs"
        >
          <span className="uppercase tracking-[0.12em] text-faint">{k}</span>
          <span className="tnum text-cyan">{formatRuleValue(v)}</span>
        </span>
      ))}
    </div>
  );
}

function AlertLog({
  alerts,
  currency,
}: {
  alerts: AlertRow[];
  currency: string | null;
}) {
  if (alerts.length === 0) {
    return <EmptyState title="No alerts have fired for this watch yet." />;
  }
  return (
    <ul className="panel divide-y divide-line">
      {alerts.map((a) => (
        <li
          key={a.id}
          className="flex flex-wrap items-center justify-between gap-3 px-4 py-3"
        >
          <div className="min-w-0">
            <p className="font-mono text-xs uppercase tracking-[0.12em] text-fg">
              {a.ruleType}
            </p>
            <p className="mt-0.5 font-mono text-[0.7rem] text-faint">
              {formatDate(a.triggeredAt)}
            </p>
          </div>
          <div className="flex items-center gap-3">
            <span className="tnum text-sm text-muted">
              {formatPrice(a.previousPrice, currency)}
              <span className="px-1.5 text-faint">→</span>
              <span className="text-fg">{formatPrice(a.newPrice, currency)}</span>
            </span>
            <span className="border border-line px-2 py-0.5 font-mono text-[0.6rem] uppercase tracking-[0.12em] text-faint">
              {a.deliveryStatus}
            </span>
          </div>
        </li>
      ))}
    </ul>
  );
}
