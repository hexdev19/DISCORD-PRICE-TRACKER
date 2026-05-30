"use client";

import { Suspense, useState } from "react";
import { useSearchParams } from "next/navigation";
import { X } from "lucide-react";

const MESSAGES: Record<string, string> = {
  "auth:cancelled": "Sign-in was cancelled.",
  "auth:error": "Sign-in failed. Please try again.",
  "bot:cancelled": "Bot authorization was cancelled.",
  "bot:error": "Couldn't add the bot. Please try again.",
};

function NoticeInner() {
  const params = useSearchParams();
  const key = params.get("auth")
    ? `auth:${params.get("auth")}`
    : params.get("bot")
      ? `bot:${params.get("bot")}`
      : null;
  const [open, setOpen] = useState(true);

  const message = key ? MESSAGES[key] : undefined;
  if (!message || !open) return null;

  return (
    <div className="fixed inset-x-0 top-[4.5rem] z-40 flex justify-center px-5">
      <div className="panel mt-3 flex items-center gap-4 px-4 py-2.5">
        <span className="beacon" aria-hidden />
        <p className="text-sm text-muted">{message}</p>
        <button
          type="button"
          onClick={() => setOpen(false)}
          aria-label="Dismiss"
          className="text-faint transition-colors hover:text-cyan focus-visible:outline-2"
        >
          <X className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
}

export function AuthNotice() {
  return (
    <Suspense fallback={null}>
      <NoticeInner />
    </Suspense>
  );
}
