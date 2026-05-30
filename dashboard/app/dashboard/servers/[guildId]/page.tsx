"use client";

import Link from "next/link";
import { use } from "react";
import { ChevronRight } from "lucide-react";
import { getServer, getWatches } from "@/lib/api";
import { useAsync } from "@/lib/use-async";
import {
  EmptyState,
  ErrorPanel,
  Skeleton,
} from "@/components/dashboard/states";
import {
  AdminBadge,
  formatPrice,
  PageHeader,
  StatusPill,
  StockPill,
} from "@/components/dashboard/page-header";

export default function ServerPage({
  params,
}: {
  params: Promise<{ guildId: string }>;
}) {
  const { guildId } = use(params);
  const server = useAsync(() => getServer(guildId), [guildId]);
  const watches = useAsync(() => getWatches(guildId), [guildId]);

  if (server.error) {
    return (
      <>
        <PageHeader
          eyebrow="Server"
          title="Dashboard"
          back={{ href: "/dashboard", label: "All servers" }}
        />
        <ErrorPanel error={server.error} onRetry={server.reload} />
      </>
    );
  }

  return (
    <>
      <PageHeader
        eyebrow="Server overview"
        title={server.data?.name ?? (server.loading ? "Loading…" : "Server")}
        back={{ href: "/dashboard", label: "All servers" }}
      >
        {server.data && (
          <div className="flex flex-wrap items-center gap-2">
            <AdminBadge isAdmin={server.data.isAdmin} />
            {server.data.regionDefault && (
              <span className="border border-line px-2 py-0.5 font-mono text-[0.65rem] uppercase tracking-[0.12em] text-muted">
                {server.data.regionDefault}
              </span>
            )}
            <span className="border border-line px-2 py-0.5 font-mono text-[0.65rem] uppercase tracking-[0.12em] text-faint">
              <span className="tnum text-muted">{server.data.watchCount}</span>{" "}
              watches
            </span>
          </div>
        )}
      </PageHeader>

      {watches.loading ? (
        <Skeleton className="h-64 w-full" />
      ) : watches.error ? (
        <ErrorPanel error={watches.error} onRetry={watches.reload} />
      ) : !watches.data || watches.data.length === 0 ? (
        <EmptyState title="No watches yet. Use /track <url> in Discord." />
      ) : (
        <div className="panel overflow-x-auto">
          <table className="w-full min-w-[640px] border-collapse text-sm">
            <thead>
              <tr className="border-b border-line text-left">
                {["Product", "Price", "Stock", "Status", ""].map((h, i) => (
                  <th
                    key={i}
                    className="px-4 py-3 font-mono text-[0.65rem] uppercase tracking-[0.16em] text-faint"
                  >
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {watches.data.map((w) => (
                <tr
                  key={w.id}
                  className="group border-b border-line transition-colors last:border-0 hover:bg-ink-2"
                >
                  <td className="px-4 py-3">
                    <Link
                      href={`/dashboard/watches/${w.id}`}
                      className="block min-w-0"
                    >
                      <p className="truncate font-medium text-fg group-hover:text-cyan">
                        {w.title ?? w.sourceUrl}
                      </p>
                      <p className="mt-0.5 font-mono text-[0.7rem] text-faint">
                        {w.domain}
                      </p>
                    </Link>
                  </td>
                  <td className="px-4 py-3">
                    <span className="tnum text-fg">
                      {formatPrice(w.lastPrice, w.currency)}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <StockPill inStock={w.inStock} />
                  </td>
                  <td className="px-4 py-3">
                    <StatusPill isActive={w.isActive} paused={w.paused} />
                  </td>
                  <td className="px-4 py-3 text-right">
                    <Link
                      href={`/dashboard/watches/${w.id}`}
                      aria-label="Open watch"
                      className="inline-flex text-faint transition-colors hover:text-cyan"
                    >
                      <ChevronRight className="h-4 w-4" />
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </>
  );
}
