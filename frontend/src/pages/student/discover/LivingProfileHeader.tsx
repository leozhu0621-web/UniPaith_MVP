/**
 * Header for the "What Uni knows about you" living profile — the eyebrow label
 * plus a live count badge that beats once when it grows (never on the initial
 * load for a returning student). Shared so the count shows wherever the living
 * profile does: the rail (mobile sheet + lg) and the xl+ right column.
 */
import { useEffect, useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import clsx from "clsx";

import { getLivingProfile } from "../../../api/livingProfile";
import type { LivingProfile } from "../../../api/livingProfile";

export default function LivingProfileHeader() {
  const { data: living } = useQuery<LivingProfile>({
    queryKey: ["discovery", "livingProfile"],
    queryFn: getLivingProfile,
  });
  const livingCount = living
    ? living.lightsUp.length + living.goals.length + living.needs.length
    : null;
  const prevCount = useRef<number | null>(null);
  const [countBeat, setCountBeat] = useState(false);
  useEffect(() => {
    if (livingCount == null) return;
    if (prevCount.current == null) {
      prevCount.current = livingCount;
      return;
    }
    if (livingCount > prevCount.current) {
      prevCount.current = livingCount;
      setCountBeat(true);
      const t = setTimeout(() => setCountBeat(false), 420);
      return () => clearTimeout(t);
    }
    prevCount.current = livingCount;
  }, [livingCount]);

  return (
    <div className="flex items-center justify-between mb-3">
      <p className="text-eyebrow text-muted-foreground">What Uni knows about you</p>
      {livingCount != null && livingCount > 0 && (
        <span
          className={clsx(
            "rounded-full bg-secondary/10 text-secondary px-2 py-0.5 text-xs font-medium",
            countBeat && "animate-beat",
          )}
          aria-label={`${livingCount} things learned`}
        >
          {livingCount}
        </span>
      )}
    </div>
  );
}
