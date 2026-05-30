"use client";

import { useEffect } from "react";
import { ApiError, getMe, loginUrl } from "@/lib/api";
import { useAsync } from "@/lib/use-async";
import { MeProvider } from "@/components/dashboard/me-context";
import { AppBar } from "@/components/dashboard/app-bar";
import { ErrorPanel, Skeleton } from "@/components/dashboard/states";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { data: me, error, loading, reload } = useAsync(getMe, []);

  useEffect(() => {
    if (error instanceof ApiError && error.status === 401) {
      window.location.href = loginUrl;
    }
  }, [error]);

  if (loading || (error instanceof ApiError && error.status === 401)) {
    return (
      <div className="mx-auto max-w-6xl px-5 py-6 sm:px-6">
        <Skeleton className="h-16 w-full" />
        <Skeleton className="mt-6 h-64 w-full" />
      </div>
    );
  }

  if (error || !me) {
    return (
      <div className="mx-auto max-w-6xl px-5 py-10 sm:px-6">
        <ErrorPanel error={error} onRetry={reload} />
      </div>
    );
  }

  return (
    <MeProvider me={me}>
      <AppBar />
      <main className="mx-auto max-w-6xl px-5 py-8 sm:px-6">{children}</main>
    </MeProvider>
  );
}
