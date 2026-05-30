import { AlertTriangle, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { ApiError } from "@/lib/api";

export function Skeleton({ className }: { className?: string }) {
  return (
    <div
      className={cn("animate-pulse border border-line bg-ink-1", className)}
      aria-hidden
    />
  );
}

export function Spinner({ label = "Loading" }: { label?: string }) {
  return (
    <div className="flex items-center gap-3 font-mono text-xs uppercase tracking-[0.18em] text-faint">
      <Loader2 className="h-4 w-4 animate-spin" />
      {label}
    </div>
  );
}

export function ErrorPanel({
  error,
  onRetry,
}: {
  error: unknown;
  onRetry?: () => void;
}) {
  const status = error instanceof ApiError ? error.status : undefined;
  const message =
    status === 403
      ? "You don't have access to this server's dashboard."
      : status === 404
        ? "We couldn't find what you were looking for."
        : "Something went wrong while loading this view.";

  return (
    <div className="panel flex flex-col items-start gap-4 p-6">
      <div className="flex items-center gap-3 text-fg">
        <AlertTriangle className="h-5 w-5 text-cyan" />
        <span className="font-mono text-xs uppercase tracking-[0.18em] text-faint">
          {status ? `Error ${status}` : "Error"}
        </span>
      </div>
      <p className="text-sm text-muted">{message}</p>
      {onRetry && (
        <button
          type="button"
          onClick={onRetry}
          className="border border-line-strong px-4 py-2 font-mono text-xs uppercase tracking-[0.12em] text-fg transition-colors hover:border-cyan hover:text-cyan"
        >
          Retry
        </button>
      )}
    </div>
  );
}

export function EmptyState({
  title,
  children,
}: {
  title: string;
  children?: React.ReactNode;
}) {
  return (
    <div className="panel flex flex-col items-start gap-4 p-8">
      <span className="eyebrow">No data</span>
      <p className="text-balance text-sm text-muted">{title}</p>
      {children}
    </div>
  );
}
