"use client";

import Link from "next/link";
import { useState } from "react";
import { Menu, X } from "lucide-react";
import { TrackerMark, Wordmark } from "./logo";
import { PrimaryButton } from "./buttons";
import { inviteUrl } from "@/lib/api";

const LINKS = [
  { label: "Features", href: "#features" },
  { label: "How it works", href: "#how" },
  { label: "Dashboard", href: "#dashboard" },
];

export function SiteNav() {
  const [open, setOpen] = useState(false);

  return (
    <header className="fixed inset-x-0 top-0 z-50 border-b border-line bg-ink">
      <nav className="mx-auto flex h-[4.5rem] max-w-6xl items-center justify-between gap-6 px-5 sm:px-6">
        <Link
          href="/"
          className="group flex items-center gap-3"
          aria-label="Price Tracker home"
        >
          <span className="grid h-9 w-9 place-items-center border border-line-strong transition-colors duration-200 group-hover:border-cyan">
            <TrackerMark className="h-5 w-5" />
          </span>
          <Wordmark className="text-[0.85rem]" />
        </Link>

        <div className="hidden items-center gap-1 md:flex">
          {LINKS.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className="px-3.5 py-2 font-mono text-xs uppercase tracking-[0.14em] text-muted transition-colors duration-150 hover:text-cyan"
            >
              {link.label}
            </Link>
          ))}
        </div>

        <div className="hidden md:block">
          <PrimaryButton href={inviteUrl} size="lg">
            Add to Discord
          </PrimaryButton>
        </div>

        <button
          type="button"
          onClick={() => setOpen((v) => !v)}
          className="flex h-10 w-10 items-center justify-center border border-line-strong text-fg transition-colors hover:border-cyan hover:text-cyan md:hidden"
          aria-label={open ? "Close menu" : "Open menu"}
          aria-expanded={open}
        >
          {open ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
        </button>
      </nav>

      {open && (
        <div className="border-t border-line bg-ink md:hidden">
          <div className="mx-auto flex max-w-6xl flex-col px-5 py-3">
            {LINKS.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                onClick={() => setOpen(false)}
                className="border-b border-line py-3 font-mono text-xs uppercase tracking-[0.14em] text-muted transition-colors hover:text-cyan"
              >
                {link.label}
              </Link>
            ))}
            <div className="mt-4">
              <PrimaryButton href={inviteUrl} className="w-full" size="lg">
                Add to Discord
              </PrimaryButton>
            </div>
          </div>
        </div>
      )}
    </header>
  );
}
