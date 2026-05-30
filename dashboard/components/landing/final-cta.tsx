import { PrimaryButton, GhostButton } from "./buttons";
import { Reveal } from "./reveal";
import { TrackerMark } from "./logo";

export function FinalCta() {
  return (
    <section className="px-5 py-12">
      <Reveal className="mx-auto max-w-5xl">
        <div className=" bg-inherit px-8 py-20 text-center sm:px-16">
          <span className="mx-auto grid h-14 w-14 place-items-center border border-cyan">
            <TrackerMark className="h-7 w-7" />
          </span>
          <h2 className="mx-auto mt-8 max-w-2xl font-pixel text-[clamp(1.5rem,4vw,2.9rem)] leading-[1.15]">
            Put a price watchdog in your server
          </h2>
          <p className="mx-auto mt-6 max-w-lg text-muted">
            Free to start. No card. Add Price Tracker, run one command, and let
            your channel catch the next drop for you.
          </p>
          <div className="mt-9 flex flex-wrap justify-center gap-3">
            <PrimaryButton href="/invite" size="lg">
              Add to Discord
            </PrimaryButton>
            <GhostButton href="#how" size="lg">
              See how it works
            </GhostButton>
          </div>
        </div>
      </Reveal>
    </section>
  );
}
