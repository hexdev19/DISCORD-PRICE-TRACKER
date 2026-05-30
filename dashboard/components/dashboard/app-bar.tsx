"use client";

import Link from "next/link";
import Image from "next/image";
import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { ChevronDown, LogOut, Plus } from "lucide-react";
import { TrackerMark, Wordmark } from "@/components/landing/logo";
import { useMe } from "./me-context";
import { avatarUrl, inviteUrl, logout } from "@/lib/api";

export function AppBar() {
  const me = useMe();
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const onClick = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setOpen(false);
    };
    document.addEventListener("mousedown", onClick);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onClick);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  async function onLogout() {
    try {
      await logout();
    } finally {
      router.replace("/");
    }
  }

  return (
    <header className="sticky top-0 z-50 border-b border-line bg-ink">
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between gap-6 px-5 sm:px-6">
        <Link
          href="/dashboard"
          className="group flex items-center gap-3"
          aria-label="Price Tracker dashboard"
        >
          <span className="grid h-9 w-9 place-items-center border border-line-strong transition-colors duration-200 group-hover:border-cyan">
            <TrackerMark className="h-5 w-5" />
          </span>
          <Wordmark className="text-[0.85rem]" />
        </Link>

        <div className="relative" ref={ref}>
          <button
            type="button"
            onClick={() => setOpen((v) => !v)}
            className="flex items-center gap-2 border border-line-strong p-1 pr-2 text-fg transition-colors hover:border-cyan focus-visible:outline-2"
            aria-haspopup="menu"
            aria-expanded={open}
            aria-label="Account menu"
          >
            <Image
              src={avatarUrl(me)}
              alt=""
              width={28}
              height={28}
              className="h-7 w-7 select-none"
              unoptimized
            />
            <ChevronDown className="h-3.5 w-3.5 text-faint" />
          </button>

          {open && (
            <div
              role="menu"
              className="panel absolute right-0 mt-2 w-64 p-1"
            >
              <div className="border-b border-line px-3 py-3">
                <p className="truncate text-sm font-semibold text-fg">
                  {me.username ?? "Discord user"}
                </p>
                {me.email && (
                  <p className="truncate font-mono text-[0.7rem] text-faint">
                    {me.email}
                  </p>
                )}
              </div>
              <a
                href={inviteUrl}
                role="menuitem"
                className="flex items-center gap-2.5 px-3 py-2.5 font-mono text-xs uppercase tracking-[0.12em] text-muted transition-colors hover:bg-ink-2 hover:text-cyan focus-visible:outline-2"
              >
                <Plus className="h-4 w-4" />
                Add to a server
              </a>
              <button
                type="button"
                role="menuitem"
                onClick={onLogout}
                className="flex w-full items-center gap-2.5 px-3 py-2.5 font-mono text-xs uppercase tracking-[0.12em] text-muted transition-colors hover:bg-ink-2 hover:text-cyan focus-visible:outline-2"
              >
                <LogOut className="h-4 w-4" />
                Logout
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
