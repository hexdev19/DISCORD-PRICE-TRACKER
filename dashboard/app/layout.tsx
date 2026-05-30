import type { Metadata, Viewport } from "next";
import { Archivo, Martian_Mono, Silkscreen } from "next/font/google";
// @ts-expect-error -- Next.js handles global CSS side-effect imports.
import "./globals.css";

const archivo = Archivo({
  subsets: ["latin"],
  variable: "--font-archivo",
  display: "swap",
});

const mono = Martian_Mono({
  subsets: ["latin"],
  variable: "--font-martian",
  display: "swap",
});

const pixel = Silkscreen({
  subsets: ["latin"],
  weight: ["400", "700"],
  variable: "--font-silkscreen",
  display: "swap",
});

const SITE = "https://pricetracker.bot";

export const metadata: Metadata = {
  metadataBase: new URL(SITE),
  title: {
    default: "Price Tracker — price-drop alerts for your Discord",
    template: "%s · Price Tracker",
  },
  description:
    "Price Tracker is a Discord bot that watches product prices across Amazon, eBay, Walmart and more, then pings your server the moment a price drops or a sold-out item is back in stock.",
  keywords: [
    "discord price tracker",
    "price drop alerts",
    "discord bot",
    "deal alerts",
    "stock alerts",
  ],
  openGraph: {
    type: "website",
    url: SITE,
    title: "Price Tracker — price-drop alerts for your Discord",
    description:
      "Track any product. Get pinged the second it drops. A Discord-first price watchdog with a read-only analytics dashboard.",
    siteName: "Price Tracker",
  },
  twitter: {
    card: "summary_large_image",
    title: "Price Tracker — price-drop alerts for your Discord",
    description: "Track any product. Get pinged the second it drops.",
  },
  robots: { index: true, follow: true },
};

export const viewport: Viewport = {
  themeColor: "#16181d",
  colorScheme: "dark",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html
      lang="en"
      className={`${archivo.variable} ${mono.variable} ${pixel.variable}`}
    >
      <body>
        <div className="grid-bg" aria-hidden />
        <div className="relative z-10">{children}</div>
      </body>
    </html>
  );
}
