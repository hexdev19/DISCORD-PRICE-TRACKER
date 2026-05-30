import Link from "next/link";
import { TrackerMark } from "./logo";
import { PrimaryButton } from "./buttons";
import { inviteUrl } from "@/lib/api";

const COLUMNS = [
  {
    title: "Product",
    links: [
      { label: "Features", href: "#features" },
      { label: "Dashboard", href: "#dashboard" },
      { label: "How it works", href: "#how" },
      { label: "Status", href: "/status" },
    ],
  },
  {
    title: "Company",
    links: [
      { label: "About", href: "/about" },
      { label: "Privacy", href: "/legal/privacy" },
      { label: "Terms", href: "/legal/terms" },
    ],
  },
  {
    title: "Community",
    links: [
      { label: "Discord", href: "/invite" },
      { label: "X", href: "https://x.com" },
      { label: "GitHub", href: "https://github.com" },
    ],
  },
];

export function SiteFooter() {
  return (
    <footer className="relative z-10 border-t-2 border-line-strong bg-ink">
      <div className="mx-auto max-w-6xl px-5 sm:px-6">
        {/* strong top band */}
        <div className="flex flex-col gap-6 border-b border-line py-12 md:flex-row md:items-center md:justify-between">
          <div className="flex items-center gap-4">
            <span className="grid h-12 w-12 place-items-center border border-cyan">
              <TrackerMark className="h-6 w-6" />
            </span>
            <div>
              <p className="font-pixel text-base uppercase tracking-[0.06em]">
                Price&nbsp;Tracker
              </p>
              <p className="mt-1 font-mono text-xs text-faint">
                Price-drop alerts, straight to Discord.
              </p>
            </div>
          </div>
          <PrimaryButton href={inviteUrl} size="lg">
            Add to Discord
          </PrimaryButton>
        </div>
    </div>
        
    </footer>
  );
}
