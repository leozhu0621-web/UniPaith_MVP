/**
 * Detects guided-journey milestones *as they happen* so the UI can fire the
 * earned-gold beat once (never on initial load for a returning student).
 *
 * Compares the current done-stage set + matches-unlock against the previous
 * render. The baseline is only recorded once the journey data has settled
 * (`ready`) — recording it while completion/handoff are still loading would
 * leave the baseline empty, so a returning student's already-finished stages
 * would all look like fresh transitions and fire stale celebrations at once.
 * Each detected transition is held for one --dur-slow window, then cleared, so
 * the `animate-beat` class can mount → play → unmount cleanly.
 */
import { useEffect, useRef, useState } from "react";

import type { JourneyStage, StageKey } from "./useJourneyState";

const HOLD_MS = 420; // --dur-slow (360ms) + a small tail so the beat finishes

export function useMilestoneBeat(stages: JourneyStage[], matchesUnlocked: boolean, ready = true) {
  const doneKeys = stages.filter((s) => s.state === "done").map((s) => s.key);
  const sig = `${doneKeys.slice().sort().join(",")}|${matchesUnlocked}`;

  const initialized = useRef(false);
  const prevDone = useRef<Set<StageKey>>(new Set());
  const prevMatches = useRef(false);
  const [newlyDone, setNewlyDone] = useState<Set<StageKey>>(new Set());
  const [matchesJustUnlocked, setMatchesJustUnlocked] = useState(false);

  useEffect(() => {
    // Wait for settled data before baselining, so the initial load of a
    // returning student isn't mistaken for a burst of fresh milestones.
    if (!ready) return;
    const done = new Set(doneKeys);
    if (!initialized.current) {
      prevDone.current = done;
      prevMatches.current = matchesUnlocked;
      initialized.current = true;
      return;
    }
    const fresh = new Set<StageKey>();
    done.forEach((k) => {
      if (!prevDone.current.has(k)) fresh.add(k);
    });
    const matchesFresh = matchesUnlocked && !prevMatches.current;
    prevDone.current = done;
    prevMatches.current = matchesUnlocked;
    if (fresh.size === 0 && !matchesFresh) return;
    if (fresh.size > 0) setNewlyDone(fresh);
    if (matchesFresh) setMatchesJustUnlocked(true);
    const t = setTimeout(() => {
      setNewlyDone(new Set());
      setMatchesJustUnlocked(false);
    }, HOLD_MS);
    return () => clearTimeout(t);
    // doneKeys/matchesUnlocked are encoded in `sig`; depend on it to avoid
    // running the body on every unrelated re-render.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sig, ready]);

  return { newlyDone, matchesJustUnlocked };
}
