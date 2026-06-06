/**
 * Spec 44 §4.2 / §6.2 — per-program apply-ready checklist (Apply workspace).
 *
 * Reads the Adaptive Intake Engine's apply-ready gate for this program and
 * renders the per-requirement checklist with the `ready_to_submit` boolean —
 * the engine's view of whether the student's signals satisfy *this program's*
 * requirements (core profile, recommenders, tests, portfolio, visa, essays).
 * Additive to the existing Spec-15 checklist; uses adaptive semantic tokens so
 * it reads correctly in light and dark.
 */
import { useQuery } from "@tanstack/react-query";
import { Check, Circle, ShieldCheck } from "lucide-react";
import clsx from "clsx";

import { getApplyReady } from "../../../api/intake";
import Card from "../../../components/ui/Card";
import Skeleton from "../../../components/ui/Skeleton";

export default function ApplyReadyChecklist({ programId }: { programId?: string | null }) {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["intake", "apply-ready", programId],
    queryFn: () => getApplyReady(programId as string),
    enabled: !!programId,
  });

  if (!programId) return null;

  if (isLoading) {
    return (
      <Card className="space-y-2 p-4">
        <Skeleton className="h-4 w-32" />
        <Skeleton className="h-3 w-full" />
        <Skeleton className="h-3 w-2/3" />
      </Card>
    );
  }

  if (isError || !data) return null;

  const ready = data.ready_to_submit;

  return (
    <Card className="space-y-3 p-4">
      <div className="flex items-center gap-2">
        <ShieldCheck size={15} className={ready ? "text-success" : "text-secondary"} />
        <h3 className="text-sm font-medium text-foreground">Apply-readiness</h3>
        <span
          className={clsx(
            "ml-auto rounded-full px-2 py-0.5 text-[11px] font-medium",
            ready ? "bg-success/10 text-success" : "bg-muted text-muted-foreground",
          )}
        >
          {ready ? "Ready to submit" : "In progress"}
        </span>
      </div>

      <ul className="space-y-1.5">
        {data.requirements.map((req) => (
          <li key={req.key} className="flex items-start gap-2 text-sm">
            {req.satisfied ? (
              <Check size={14} className="mt-0.5 shrink-0 text-success" />
            ) : (
              <Circle size={12} className="mt-1 shrink-0 text-muted-foreground" />
            )}
            <div className="min-w-0 flex-1">
              <span className={clsx(req.satisfied ? "text-muted-foreground" : "text-foreground")}>
                {req.label}
              </span>
              {req.detail && (
                <span className="ml-1.5 text-xs text-muted-foreground">· {req.detail}</span>
              )}
              {req.advisory && (
                <span className="ml-1.5 text-[11px] text-muted-foreground">(optional gate)</span>
              )}
            </div>
          </li>
        ))}
      </ul>

      <p className="text-xs text-muted-foreground">
        {ready
          ? "Your profile signals satisfy this program’s requirements."
          : "Complete the open items above to clear the engine’s apply-ready gate."}
      </p>
    </Card>
  );
}
