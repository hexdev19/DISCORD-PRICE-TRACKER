import Image from "next/image";
import { PrimaryButton, GhostButton } from "./buttons";
import { Reveal } from "./reveal";
import { inviteUrl } from "@/lib/api";

/** Targeting-scope reticle drawn behind the mascot. Pure decoration. */
function HeroReticle() {
  const c = "oklch(0.8 0.13 215";
  return (
    <svg
      viewBox="0 0 200 200"
      className="absolute inset-0 h-full w-full"
      fill="none"
      aria-hidden
    >
      {/* crosshair, broken at the center */}
      <g stroke={`${c} / 0.16)`} strokeWidth="1">
        <line x1="100" y1="6" x2="100" y2="74" />
        <line x1="100" y1="126" x2="100" y2="194" />
        <line x1="6" y1="100" x2="74" y2="100" />
        <line x1="126" y1="100" x2="194" y2="100" />
      </g>
      {/* mid ring + center pip */}
      <circle cx="100" cy="100" r="56" stroke={`${c} / 0.12)`} strokeWidth="1" />
      <circle cx="100" cy="100" r="5" stroke={`${c} / 0.45)`} strokeWidth="1" />
      <circle cx="100" cy="100" r="1.4" fill={`${c} / 0.6)`} />
      {/* spinning outer ring with cardinal ticks */}
      <g className="reticle-spin">
        <circle
          cx="100"
          cy="100"
          r="86"
          stroke={`${c} / 0.22)`}
          strokeWidth="1"
          strokeDasharray="2 7"
        />
        <g stroke={`${c} / 0.4)`} strokeWidth="1.5">
          <line x1="100" y1="6" x2="100" y2="16" />
          <line x1="100" y1="184" x2="100" y2="194" />
          <line x1="6" y1="100" x2="16" y2="100" />
          <line x1="184" y1="100" x2="194" y2="100" />
        </g>
      </g>
    </svg>
  );
}

export function Hero() {
  return (
    <section className="relative flex min-h-[100svh] flex-col items-center justify-center overflow-hidden px-5 pb-8 pt-20 text-center">
      {/* hero atmosphere (scoped to the hero only) */}
      <div className="hero-glow" aria-hidden />
      <div className="hero-scanlines" aria-hidden />
      <div className="hero-noise" aria-hidden />

      {/* brutal geometric framing */}
      <span className="pointer-events-none absolute left-5 top-20 h-10 w-10 border-l-2 border-t-2 border-line-strong" aria-hidden />
      <span className="pointer-events-none absolute right-5 top-20 h-10 w-10 border-r-2 border-t-2 border-line-strong" aria-hidden />
      <span className="pointer-events-none absolute bottom-5 left-5 h-10 w-10 border-b-2 border-l-2 border-line-strong" aria-hidden />
      <span className="pointer-events-none absolute bottom-5 right-5 h-10 w-10 border-b-2 border-r-2 border-line-strong" aria-hidden />

      {/* edge telemetry */}
      <span className="pointer-events-none absolute left-6 top-24 hidden font-mono text-[0.65rem] uppercase tracking-[0.2em] text-faint sm:block" aria-hidden>
        sys // price-tracker
      </span>
      <span className="pointer-events-none absolute right-6 top-24 hidden font-mono text-[0.65rem] uppercase tracking-[0.2em] text-faint sm:block" aria-hidden>
        rev 2.6
      </span>
      <span className="pointer-events-none absolute bottom-6 left-6 hidden font-mono text-[0.65rem] uppercase tracking-[0.2em] text-faint sm:block" aria-hidden>
        unit // pt-01
      </span>
      <span className="pointer-events-none absolute bottom-6 right-6 hidden font-mono text-[0.65rem] uppercase tracking-[0.2em] text-faint sm:block" aria-hidden>
        [ live · 24/7 ]
      </span>

      {/* vertical rail + offbeat crosshairs */}
      <span className="rail-y pointer-events-none absolute left-7 top-1/2 hidden -translate-y-1/2 font-mono text-[0.6rem] uppercase tracking-[0.3em] text-faint lg:block" aria-hidden>
        price-tracker · est. 2026
      </span>
      <span className="pointer-events-none absolute left-[19%] top-[31%] hidden font-mono text-base text-faint lg:block" aria-hidden>+</span>
      <span className="pointer-events-none absolute right-[17%] bottom-[27%] hidden font-mono text-base text-faint lg:block" aria-hidden>+</span>

      <div className="relative z-10 flex w-full max-w-4xl flex-col items-center">
        <Reveal>
          <span className="inline-flex items-center gap-3 border border-line bg-ink-1 px-4 py-1.5 font-mono text-[0.7rem] uppercase tracking-[0.2em] text-muted">
            <span className="text-faint">[</span>
            <span className="beacon" />
            Watching 6 retailers
            <span className="h-3 w-px bg-line-strong" aria-hidden />
            <span className="text-cyan">live 24/7</span>
            <span className="text-faint">]</span>
          </span>
        </Reveal>

        <Reveal delay={60}>
          <div className="relative mt-[clamp(0.7rem,2.2vh,1.5rem)]">
            <span className="pointer-events-none absolute -right-4 -top-1 hidden font-mono text-sm text-faint sm:block" aria-hidden>®</span>
            <h1 className="title-hermes font-pixel leading-[1.04] tracking-tight">
              <span className="block whitespace-nowrap text-[clamp(2.5rem,min(12vw,14vh),7.5rem)]">
                Price-Tracker
              </span>
            </h1>
          </div>
        </Reveal>

        {/* spec ribbon */}
        <Reveal delay={100}>
          <div className="mt-[clamp(0.65rem,1.6vh,1rem)] flex items-center justify-center gap-3 font-mono text-[0.62rem] uppercase tracking-[0.22em] text-faint">
            <span className="h-px w-8 bg-line-strong" aria-hidden />
            <span>6 stores</span>
            <span className="text-cyan">·</span>
            <span>24/7 scan</span>
            <span className="text-cyan">·</span>
            <span>alerts &lt;1s</span>
            <span className="h-px w-8 bg-line-strong" aria-hidden />
          </div>
        </Reveal>

        <Reveal delay={140}>
          <p className="mt-[clamp(0.7rem,1.9vh,1.35rem)] max-w-lg text-balance text-[clamp(0.95rem,1.3vw,1.1rem)] leading-relaxed text-muted">
            A Discord bot that tracks any product&apos;s price across every major
            store, and pings your server{" "}
            <span className="text-cyan">the second it drops</span>.
          </p>
        </Reveal>

        {/* the mascot: locked inside a targeting scope */}
        <Reveal delay={200}>
          <div className="relative mt-[clamp(0.9rem,2.6vh,2rem)] inline-block">
            {/* reticle + radar sweep, clipped to a soft disc behind the bot */}
            <div
              className="hero-field pointer-events-none absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 overflow-hidden"
              style={{
                width: "clamp(9.5rem,23vh,15rem)",
                height: "clamp(9.5rem,23vh,15rem)",
              }}
              aria-hidden
            >
              <HeroReticle />
              <span className="hero-scan" />
            </div>

            {/* cyan corner ticks hugging the bot */}
            <span className="absolute -left-4 -top-4 z-20 h-6 w-6 border-l-2 border-t-2 border-cyan" aria-hidden />
            <span className="absolute -right-4 -top-4 z-20 h-6 w-6 border-r-2 border-t-2 border-cyan" aria-hidden />
            <span className="absolute -bottom-4 -left-4 z-20 h-6 w-6 border-b-2 border-l-2 border-cyan" aria-hidden />
            <span className="absolute -bottom-4 -right-4 z-20 h-6 w-6 border-b-2 border-r-2 border-cyan" aria-hidden />

            {/* grounding shadow */}
            <div
              className="pointer-events-none absolute -bottom-3 left-1/2 z-0 h-6 w-[60%] -translate-x-1/2 rounded-[50%]"
              style={{
                background:
                  "radial-gradient(ellipse at center, oklch(0 0 0 / 0.6), transparent 70%)",
              }}
              aria-hidden
            />

            <Image
              src="/bot.png"
              alt="Price Tracker bot mascot"
              width={600}
              height={600}
              priority
              className="float-bot relative z-10 h-[clamp(6.75rem,17vh,11.5rem)] w-auto select-none"
            />

          

          </div>
        </Reveal>

        <Reveal delay={260}>
          <div className="mt-[clamp(1.1rem,2.8vh,2rem)] flex flex-wrap items-center justify-center gap-3">
            <PrimaryButton href={inviteUrl} size="lg">
              Add to Discord
            </PrimaryButton>
            <GhostButton href="#how" size="lg">
              How it works
            </GhostButton>
          </div>
        </Reveal>

        <Reveal delay={300}>
          <p className="mt-3 font-mono text-[0.6rem] uppercase tracking-[0.22em] text-faint">
            No credit card · 30-second setup · Free forever
          </p>
        </Reveal>
      </div>
    </section>
  );
}
