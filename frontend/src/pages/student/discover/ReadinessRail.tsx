/**
 * Spec 44 §4.1 / §6 — Adaptive Intake Engine readiness rail (Discover).
 *
 * Surfaces the engine's three student-facing outputs on the Discover page:
 *   1. the match-ready gate — "N more to unlock your first matches", with inline
 *      quick-fill for each missing signal, flipping to a gold "you're match-ready"
 *      beat + Generate-strategy CTA when the gate clears (§4.1);
 *   2. per-category completeness bars (§4);
 *   3. the low-confidence clarification confirm/correct loop (§6).
 *
 * Tokens are adaptive semantic (`foreground`/`muted`/`border`/`primary`) so the
 * rail reads correctly in light and dark; gold (`primary`) is reserved for the
 * single earned match-ready moment.
 */
import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { CheckCircle2, Circle, HelpCircle, Sparkles, Target } from "lucide-react";
import clsx from "clsx";

import {
  formSave,
  getCompleteness,
  getMatchReady,
  listClarifications,
  resolveClarification,
  type Clarification,
  type MatchReadyMissing,
} from "../../../api/intake";
import Button from "../../../components/ui/Button";
import Card from "../../../components/ui/Card";
import QueryError from "../../../components/ui/QueryError";
import Skeleton from "../../../components/ui/Skeleton";
import { showToast } from "../../../stores/toast-store";

// ── client-side input hints for the match-ready required signals ─────────────
const ENUM_OPTIONS: Record<string, string[]> = {
  target_degree_level: ["certificate", "associate", "bachelor", "master", "mba", "phd"],
  current_academic_year_level: [
    "high_school",
    "undergraduate",
    "graduate",
    "gap_year",
    "working_professional",
  ],
  target_start_term_season: ["fall", "spring", "summer", "winter"],
  preferred_modality: ["in_person", "online", "hybrid", "no_preference"],
  budget_band_annual_total: ["0-20k", "20-40k", "40-60k", "60-80k", "80k+"],
};
const NUMBER_SIGNALS = new Set(["target_start_term_year"]);
const DATE_SIGNALS = new Set(["expected_graduation_date"]);
const PRIORITY_KEYS = [
  "cost",
  "location",
  "prestige",
  "outcomes",
  "culture",
  "flexibility",
  "support",
];

const prettyEnum = (v: string) => v.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());

function QuickFillRow({ item, onSaved }: { item: MatchReadyMissing; onSaved: () => void }) {
  const [open, setOpen] = useState(false);
  const [value, setValue] = useState("");
  const [picked, setPicked] = useState<string[]>([]);

  const save = useMutation({
    mutationFn: async () => {
      if (item.kind === "priorities") {
        const weights: Record<string, number> = {};
        picked.forEach((k, i) => (weights[k] = picked.length - i));
        return formSave("preference_weights", weights);
      }
      if (item.kind === "geography") {
        const list = value
          .split(",")
          .map((s) => s.trim())
          .filter(Boolean);
        return formSave("preferred_countries", list);
      }
      let v: unknown = value.trim();
      if (NUMBER_SIGNALS.has(item.signal_name)) v = Number(value);
      return formSave(item.signal_name, v);
    },
    onSuccess: () => {
      setOpen(false);
      setValue("");
      setPicked([]);
      onSaved();
    },
    onError: (e: unknown) => showToast((e as Error).message ?? "Could not save", "error"),
  });

  const canSave = item.kind === "priorities" ? picked.length >= 3 : value.trim().length > 0;

  const enumOpts = ENUM_OPTIONS[item.signal_name];

  return (
    <li>
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className="flex w-full items-center gap-2 px-3 py-2 text-left text-sm text-foreground hover:bg-muted/60"
      >
        <Circle size={13} className="shrink-0 text-muted-foreground" />
        <span className="flex-1">{item.label}</span>
        {item.detail && <span className="text-xs text-muted-foreground">{item.detail}</span>}
        <span className="text-xs text-secondary">{open ? "Close" : "Add"}</span>
      </button>

      {open && (
        <div className="space-y-2 border-t border-border px-3 py-2.5">
          {item.kind === "priorities" ? (
            <div className="flex flex-wrap gap-1.5">
              {PRIORITY_KEYS.map((k) => {
                const on = picked.includes(k);
                return (
                  <button
                    key={k}
                    type="button"
                    onClick={() => setPicked((p) => (on ? p.filter((x) => x !== k) : [...p, k]))}
                    className={clsx(
                      "rounded-full border px-2.5 py-1 text-xs capitalize transition-colors",
                      on
                        ? "border-secondary bg-secondary/10 text-secondary"
                        : "border-border text-muted-foreground hover:text-foreground",
                    )}
                  >
                    {k}
                  </button>
                );
              })}
            </div>
          ) : enumOpts ? (
            <select
              value={value}
              onChange={(e) => setValue(e.target.value)}
              className="w-full rounded-lg border border-border bg-background px-2.5 py-1.5 text-sm text-foreground"
            >
              <option value="">Select…</option>
              {enumOpts.map((o) => (
                <option key={o} value={o}>
                  {prettyEnum(o)}
                </option>
              ))}
            </select>
          ) : (
            <input
              type={
                DATE_SIGNALS.has(item.signal_name)
                  ? "date"
                  : NUMBER_SIGNALS.has(item.signal_name)
                    ? "number"
                    : "text"
              }
              value={value}
              onChange={(e) => setValue(e.target.value)}
              placeholder={
                item.kind === "geography" ? "e.g. United States, United Kingdom" : item.label
              }
              className="w-full rounded-lg border border-border bg-background px-2.5 py-1.5 text-sm text-foreground placeholder:text-muted-foreground"
            />
          )}
          <Button
            size="sm"
            variant="secondary"
            disabled={!canSave}
            loading={save.isPending}
            onClick={() => save.mutate()}
          >
            Save
          </Button>
        </div>
      )}
    </li>
  );
}

function ClarificationCard({ clar, onResolved }: { clar: Clarification; onResolved: () => void }) {
  const [editing, setEditing] = useState(false);
  const [value, setValue] = useState(String(clar.suggested_value ?? ""));

  const resolve = useMutation({
    mutationFn: (args: { action: "confirm" | "correct"; value?: unknown }) =>
      resolveClarification(clar.id, args.action, args.value),
    onSuccess: () => onResolved(),
    onError: (e: unknown) => showToast((e as Error).message ?? "Could not save", "error"),
  });

  return (
    <div className="rounded-lg border border-border bg-muted/40 p-3">
      <div className="flex items-start gap-2">
        <HelpCircle size={14} className="mt-0.5 shrink-0 text-secondary" />
        <p className="text-sm text-foreground">{clar.question}</p>
      </div>
      {editing ? (
        <div className="mt-2 flex gap-2">
          <input
            value={value}
            onChange={(e) => setValue(e.target.value)}
            className="flex-1 rounded-lg border border-border bg-background px-2.5 py-1.5 text-sm text-foreground"
          />
          <Button
            size="sm"
            variant="secondary"
            loading={resolve.isPending}
            onClick={() => resolve.mutate({ action: "correct", value })}
          >
            Save
          </Button>
        </div>
      ) : (
        <div className="mt-2 flex gap-2">
          <Button
            size="sm"
            variant="secondary"
            loading={resolve.isPending}
            onClick={() => resolve.mutate({ action: "confirm" })}
          >
            Yes, that's right
          </Button>
          <Button size="sm" variant="tertiary" onClick={() => setEditing(true)}>
            Fix it
          </Button>
        </div>
      )}
    </div>
  );
}

export default function ReadinessRail({
  onGenerateStrategy,
}: {
  onGenerateStrategy?: () => void
}) {
  const qc = useQueryClient();

  const matchReady = useQuery({ queryKey: ["intake", "match-ready"], queryFn: getMatchReady });
  const completeness = useQuery({ queryKey: ["intake", "completeness"], queryFn: getCompleteness });
  const clarifications = useQuery({
    queryKey: ["intake", "clarifications"],
    queryFn: listClarifications,
  });

  const refetchAll = () => {
    qc.invalidateQueries({ queryKey: ["intake"] });
    // a signal change can move matches + discovery completion downstream
    qc.invalidateQueries({ queryKey: ["matching"] });
    qc.invalidateQueries({ queryKey: ["discovery"] });
  };

  if (matchReady.isLoading || completeness.isLoading) {
    return (
      <Card pad={false} className="space-y-3 p-4">
        <Skeleton className="h-5 w-40" />
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-4 w-3/4" />
      </Card>
    );
  }

  if (matchReady.isError || completeness.isError) {
    return (
      <Card pad={false} className="p-4">
        <QueryError
          variant="inline"
          detail="Couldn't load your readiness."
          onRetry={() => {
            matchReady.refetch();
            completeness.refetch();
          }}
        />
      </Card>
    );
  }

  const mr = matchReady.data;
  const comp = completeness.data;
  const clars = clarifications.data?.clarifications ?? [];
  const ready = !!mr?.match_ready;

  return (
    <Card pad={false}
      className={clsx(
        "space-y-4 p-4 transition-colors",
        ready ? "border-primary/50 bg-primary/5" : "border-border",
      )}
    >
      {/* ── match-ready gate ── */}
      <div className="flex items-start gap-3">
        {ready ? (
          <Sparkles size={18} className="mt-0.5 shrink-0 text-primary" />
        ) : (
          <Target size={18} className="mt-0.5 shrink-0 text-secondary" />
        )}
        <div className="min-w-0 flex-1">
          <h3 className="text-sm font-semibold text-foreground">
            {ready
              ? "You're match-ready"
              : `${mr?.missing_count ?? 0} more to unlock your first matches`}
          </h3>
          <p className="mt-0.5 text-xs text-muted-foreground">
            {ready
              ? "Your profile has enough signal to generate a shortlist. Turn it into a strategy."
              : "Answer these in chat, or add them here — they're what powers your matches."}
          </p>
        </div>
        <span className="shrink-0 text-xs font-medium text-muted-foreground">
          {mr?.completeness_pct ?? 0}%
        </span>
      </div>

      {ready ? (
        <Button
          size="sm"
          variant="primary"
          className="w-full"
          onClick={() => onGenerateStrategy?.()}
        >
          <Sparkles size={14} className="mr-1" /> Generate your first strategy
        </Button>
      ) : (
        mr &&
        mr.missing.length > 0 && (
          <ul className="divide-y divide-border">
            {mr.missing.map((item) => (
              <QuickFillRow key={item.signal_name} item={item} onSaved={refetchAll} />
            ))}
          </ul>
        )
      )}

      {/* ── clarifications (§6) ── */}
      {clars.length > 0 && (
        <div className="space-y-2 border-t border-border pt-3">
          <p className="text-eyebrow text-muted-foreground">Just to confirm</p>
          {clars.map((c) => (
            <ClarificationCard key={c.id} clar={c} onResolved={refetchAll} />
          ))}
        </div>
      )}

      {/* ── completeness by category (§4) ── */}
      {comp && (
        <div className="space-y-2 border-t border-border pt-3">
          <div className="flex items-center justify-between">
            <p className="text-eyebrow text-muted-foreground">Profile completeness</p>
            <span className="text-xs text-muted-foreground">
              {comp.present_signals}/{comp.total_signals}
            </span>
          </div>
          <div className="space-y-1.5">
            {comp.categories
              .filter((c) => c.total > 0)
              .map((c) => (
                <div key={c.category} className="flex items-center gap-2">
                  <span className="w-28 shrink-0 truncate text-xs capitalize text-muted-foreground">
                    {c.category.replace(/_/g, " ")}
                  </span>
                  <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-muted">
                    <div
                      className={clsx(
                        "h-full rounded-full",
                        c.pct === 100 ? "bg-accent" : "bg-secondary",
                      )}
                      style={{ width: `${c.pct}%` }}
                    />
                  </div>
                  {c.pct === 100 && <CheckCircle2 size={12} className="shrink-0 text-accent" />}
                </div>
              ))}
          </div>
        </div>
      )}
    </Card>
  );
}
