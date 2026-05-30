"use client";

import Link from "next/link";
import Image from "next/image";
import { getServers, serverIconUrl, inviteUrl } from "@/lib/api";
import { useAsync } from "@/lib/use-async";
import { useMe } from "@/components/dashboard/me-context";
import { PrimaryButton } from "@/components/landing/buttons";
import {
  EmptyState,
  ErrorPanel,
  Skeleton,
} from "@/components/dashboard/states";
import { AdminBadge, PageHeader } from "@/components/dashboard/page-header";

export default function DashboardPage() {
  const me = useMe();
  const { data, error, loading, reload } = useAsync(getServers, []);

  return (
    <>
      <PageHeader
        eyebrow={`Signed in as ${me.username ?? "Discord user"}`}
        title="Your servers"
      />

      {loading ? (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-28" />
          ))}
        </div>
      ) : error ? (
        <ErrorPanel error={error} onRetry={reload} />
      ) : !data || data.length === 0 ? (
        <EmptyState title="Invite the bot to a server to get started.">
          <PrimaryButton href={inviteUrl}>Add to Discord</PrimaryButton>
        </EmptyState>
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {data.map((s) => {
            const icon = serverIconUrl(s);
            return (
              <Link
                key={s.guildId}
                href={`/dashboard/servers/${s.guildId}`}
                className="panel lift flex items-center gap-4 p-5"
              >
                {icon ? (
                  <Image
                    src={icon}
                    alt=""
                    width={48}
                    height={48}
                    className="h-12 w-12 shrink-0 border border-line"
                    unoptimized
                  />
                ) : (
                  <span className="grid h-12 w-12 shrink-0 place-items-center border border-line-strong font-pixel text-sm uppercase text-cyan">
                    {(s.name ?? "?").slice(0, 2)}
                  </span>
                )}
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <p className="truncate font-semibold text-fg">
                      {s.name ?? "Unknown server"}
                    </p>
                    <AdminBadge isAdmin={s.isAdmin} />
                  </div>
                  <p className="mt-1 font-mono text-xs text-faint">
                    <span className="tnum text-muted">{s.watchCount}</span>{" "}
                    {s.watchCount === 1 ? "watch" : "watches"}
                  </p>
                </div>
              </Link>
            );
          })}
        </div>
      )}
    </>
  );
}
