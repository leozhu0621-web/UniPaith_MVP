/**
 * The Uni journey rail — Stage 01 Discovery stages (each with a progress fill +
 * a once-only earned-gold beat as it completes), a Stage 02 "first look" matches
 * item that celebrates when it unlocks, and the living profile with a live "what
 * Uni knows" counter. Docked left on desktop (≥ lg); inside a bottom sheet on
 * mobile. Stage math comes from useJourneyState; milestone transitions from
 * useMilestoneBeat. Revisiting a done stage nudges the conversation via onRevisit.
 */
import clsx from "clsx";
import { Check, Lock, Sparkles } from "lucide-react";

import LivingProfileHeader from "./LivingProfileHeader";
import LivingProfilePanel from "./LivingProfilePanel";
import { useMilestoneBeat } from "./useMilestoneBeat";
import type { JourneyStage, StageKey } from "./useJourneyState";

function StageDot({ state, beat }: { state: JourneyStage["state"]; beat?: boolean }) {
  const beatCls = beat ? "animate-beat rounded-full" : "";
  if (state === "done")
    return (
      <span
        className={clsx(
          "w-4 h-4 rounded-full bg-secondary text-white flex items-center justify-center shrink-0",
          beatCls,
        )}
      >
        <Check size={10} />
      </span>
    );
  if (state === "current")
    return <span className="w-4 h-4 rounded-full border-2 border-secondary shrink-0" />;
  return (
    <span className="w-4 h-4 rounded-full border border-border flex items-center justify-center shrink-0 text-muted-foreground">
      <Lock size={9} />
    </span>
  );
}

export default function JourneyRail({
  stages,
  matchesUnlocked,
  journeyLoaded,
  onRevisit,
  onOpenMatches,
  onAsk,
}: {
  stages: JourneyStage[];
  matchesUnlocked: boolean;
  /** Only true once completion + handoff have settled, so the baseline isn't
      recorded against the loading state (which would fake fresh milestones). */
  journeyLoaded?: boolean;
  onRevisit?: (key: StageKey) => void;
  onOpenMatches?: () => void;
  onAsk?: (prompt: string) => void;
}) {
  const { newlyDone, matchesJustUnlocked } = useMilestoneBeat(
    stages,
    matchesUnlocked,
    journeyLoaded,
  );

  return (
    <div className="flex flex-col gap-6 text-sm">
      <div>
        <p className="text-eyebrow text-muted-foreground mb-3">Stage 01 · Discovery</p>
        <div className="flex flex-col gap-1.5">
          {stages.map((s) => {
            const done = s.state === "done";
            const current = s.state === "current";
            const pctLabel = Math.round(Math.min(1, Math.max(0, s.pct)) * 100);
            return (
              <button
                key={s.key}
                type="button"
                disabled={!done}
                onClick={() => done && onRevisit?.(s.key)}
                className={clsx(
                  "w-full rounded-lg px-2.5 py-2 text-left transition-colors",
                  current &&
                    "bg-secondary/10 border border-secondary/30 font-medium text-foreground",
                  done && "hover:bg-muted text-foreground",
                  s.state === "locked" && "text-muted-foreground cursor-default",
                )}
              >
                <span className="flex items-center gap-2.5">
                  <StageDot state={s.state} beat={newlyDone.has(s.key)} />
                  <span className="flex-1">{s.label}</span>
                  {current && <span className="text-xs text-secondary">now</span>}
                  {done && <span className="text-xs text-muted-foreground">{pctLabel}%</span>}
                </span>
                {(current || done) && (
                  <span className="mt-1.5 ml-[26px] block h-1 rounded-full bg-muted overflow-hidden">
                    <span
                      className="block h-full bg-secondary transition-[width] duration-500 ease-out"
                      style={{ width: `${pctLabel}%` }}
                    />
                  </span>
                )}
              </button>
            );
          })}
        </div>
      </div>

      <div>
        <p className="text-eyebrow text-muted-foreground mb-2">Stage 02 · a first look</p>
        <button
          type="button"
          disabled={!matchesUnlocked}
          onClick={() => matchesUnlocked && onOpenMatches?.()}
          className={clsx(
            "flex items-center gap-2.5 w-full rounded-lg px-2.5 py-2 text-left",
            matchesUnlocked
              ? "text-secondary hover:bg-muted border border-dashed border-secondary/40"
              : "text-muted-foreground cursor-default",
            matchesJustUnlocked && "animate-beat elev-glow !border-solid !border-primary",
          )}
        >
          <Sparkles size={15} className="shrink-0" />
          <span className="flex-1">Your matches</span>
          {matchesJustUnlocked ? (
            <span className="text-xs text-primary">unlocked</span>
          ) : (
            !matchesUnlocked && <span className="text-xs">unlocks soon</span>
          )}
        </button>
      </div>

      {/* Living profile shows in the rail on mobile (sheet) + lg; at xl+ it moves
          to its own right column in DiscoverHomePage, so hide it here then. */}
      <div className="border-t border-border pt-4 xl:hidden">
        <LivingProfileHeader />
        <LivingProfilePanel onAsk={onAsk} />
      </div>
    </div>
  );
}
