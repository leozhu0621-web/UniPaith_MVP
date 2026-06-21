/**
 * TemplateRunner — step-by-step guided session for a session template.
 *
 * Spec: docs/superpowers/specs/2026-06-19-uni-chat-tab-redesign-design.md §5
 * Design ref: .superpowers/brainstorm/65894-1781912267/content/session-templates.html
 *   (the "#running" view: slim work-order spine + Uni walking one step at a time)
 *
 * Layout:
 *   ─ Top bar: template icon + title + "Step N of M"
 *   ─ Work-order spine: steps with done / active / upcoming states
 *   ─ Conversation scroll: Uni's framing message + the current step's widget
 *   ─ Completion: artifact card when all steps are done
 *
 * Prompt steps write to the enrichment layer (setEnrichValue) — real, live.
 * Action steps show a placeholder "Uni is building…" then auto-advance after a
 * short delay and reveal a completion card.  These are explicitly a placeholder;
 * no fake school / data results are shown.
 *
 * Sub-renders step widgets using AnswerChoices (choice/multi/scale) and
 * KeywordPicker / TypeaheadPicker from EnrichWidget for those ask_kinds.
 * Plain number / date / text / range inputs are handled inline.
 */

import { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  Check,
  BookOpen,
  Flag,
  Heart,
  Compass,
  List,
  Scale,
  Calendar,
  X,
  ArrowRight,
} from "lucide-react";
import clsx from "clsx";

import {
  getChatTemplates,
  dispatchTemplateAction,
  type ChatTemplate,
  type TemplateStep,
  type ActionArtifact,
  type ActionArtifactItem,
} from "../../../api/chatTemplates";
import { setEnrichValue } from "../../../api/enrichment";
import AnswerChoices from "../discover/AnswerChoices";
import { KeywordPicker, TypeaheadPicker } from "../../../components/student/EnrichWidget";
import Button from "../../../components/ui/Button";

// ── Props ────────────────────────────────────────────────────────────────────

interface Props {
  /** The template key (matches ChatTemplate.key from the API). */
  templateKey: string;
  /** Called when the user closes / exits the runner. */
  onClose: () => void;
}

// ── Template icon map ─────────────────────────────────────────────────────────

function TemplateIcon({ icon, size = 18 }: { icon: string; size?: number }) {
  const strokeWidth = 1.7;
  const icons: Record<string, React.ReactNode> = {
    pen: <BookOpen size={size} strokeWidth={strokeWidth} />,
    flag: <Flag size={size} strokeWidth={strokeWidth} />,
    heart: <Heart size={size} strokeWidth={strokeWidth} />,
    compass: <Compass size={size} strokeWidth={strokeWidth} />,
    list: <List size={size} strokeWidth={strokeWidth} />,
    scale: <Scale size={size} strokeWidth={strokeWidth} />,
    calendar: <Calendar size={size} strokeWidth={strokeWidth} />,
    book: <BookOpen size={size} strokeWidth={strokeWidth} />,
  };
  return <>{icons[icon] ?? <BookOpen size={size} strokeWidth={strokeWidth} />}</>;
}

// ── Orb ──────────────────────────────────────────────────────────────────────

function UniOrb({ size = 40 }: { size?: number }) {
  return (
    <div
      aria-hidden="true"
      style={{
        width: size,
        height: size,
        borderRadius: "50%",
        flexShrink: 0,
        background:
          "radial-gradient(circle at 38% 34%, hsl(var(--primary)), hsl(var(--secondary)) 80%)",
        boxShadow: "0 0 14px 1px hsl(var(--primary) / 0.4)",
      }}
    />
  );
}

// ── Work-order spine ──────────────────────────────────────────────────────────

function Spine({
  steps,
  currentIndex,
}: {
  steps: TemplateStep[];
  currentIndex: number;
}) {
  return (
    <div className="flex items-center max-w-[700px] mx-auto px-6 pb-4 pt-1" aria-label="Progress">
      {steps.map((step, i) => {
        const done = i < currentIndex;
        const active = i === currentIndex;
        return (
          <div key={step.step_order} className="flex items-center flex-1 min-w-0">
            {/* Step node */}
            <div
              role="listitem"
              aria-label={`Step ${i + 1}: ${step.label}${done ? " (done)" : active ? " (current)" : ""}`}
              className="flex items-center gap-2 shrink-0"
            >
              <span
                className={clsx(
                  "flex h-6 w-6 items-center justify-center rounded-full border-2 text-[11px] font-bold transition-colors",
                  done
                    ? "border-secondary bg-secondary text-white"
                    : active
                      ? "border-secondary text-secondary bg-card"
                      : "border-border text-muted-foreground bg-card",
                )}
              >
                {done ? <Check size={11} strokeWidth={3} /> : i + 1}
              </span>
              <span
                className={clsx(
                  "text-[12.5px] font-bold hidden sm:block truncate max-w-[80px]",
                  done
                    ? "text-muted-foreground"
                    : active
                      ? "text-foreground"
                      : "text-muted-foreground",
                )}
              >
                {step.label}
              </span>
            </div>

            {/* Bar connector — not after the last step */}
            {i < steps.length - 1 && (
              <div
                className={clsx(
                  "flex-1 h-0.5 mx-2",
                  i < currentIndex ? "bg-secondary" : "bg-border",
                )}
              />
            )}
          </div>
        );
      })}
    </div>
  );
}

// ── Uni message bubble ────────────────────────────────────────────────────────

function UniTurn({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex gap-3 items-start animate-in fade-in slide-in-from-bottom-2 duration-500">
      <div className="mt-0.5">
        <UniOrb size={40} />
      </div>
      <div className="flex-1 flex flex-col gap-3 min-w-0">{children}</div>
    </div>
  );
}

// ── Step widget ───────────────────────────────────────────────────────────────

/**
 * Renders the inline input widget for a prompt step.
 * Calls onSubmit(value) on completion.
 */
function PromptStepWidget({
  step,
  onSubmit,
  disabled,
}: {
  step: TemplateStep;
  onSubmit: (value: unknown) => void;
  disabled: boolean;
}) {
  const [textVal, setTextVal] = useState("");
  const [numVal, setNumVal] = useState("");
  const [dateVal, setDateVal] = useState("");
  const [rangeMin, setRangeMin] = useState("");
  const [rangeMax, setRangeMax] = useState("");

  const askKind = step.ask_kind;
  const options = step.options ?? [];

  // choice / multi / scale — delegate to AnswerChoices
  if (askKind === "choice") {
    return (
      <div className="border border-border rounded-[14px] bg-card shadow-[0_1px_2px_rgba(10,20,40,.06)] p-4 max-w-[540px]">
        <AnswerChoices
          kind="choice"
          options={options}
          onPick={(v) => onSubmit(v)}
          disabled={disabled}
        />
      </div>
    );
  }

  if (askKind === "multi") {
    return (
      <div className="border border-border rounded-[14px] bg-card shadow-[0_1px_2px_rgba(10,20,40,.06)] p-4 max-w-[540px]">
        <AnswerChoices
          kind="multi"
          options={options}
          onPick={(v) => onSubmit(v)}
          disabled={disabled}
          asList
        />
      </div>
    );
  }

  if (askKind === "scale") {
    return (
      <div className="border border-border rounded-[14px] bg-card shadow-[0_1px_2px_rgba(10,20,40,.06)] p-4 max-w-[540px]">
        <AnswerChoices
          kind="scale"
          options={[]}
          onPick={(v) => onSubmit(v)}
          disabled={disabled}
          numeric
        />
      </div>
    );
  }

  if (askKind === "keywords") {
    return (
      <div className="border border-border rounded-[14px] bg-card shadow-[0_1px_2px_rgba(10,20,40,.06)] p-4 max-w-[540px]">
        <KeywordPicker
          options={options}
          onSubmit={(v) => onSubmit(v)}
          disabled={disabled}
        />
      </div>
    );
  }

  if (askKind === "typeahead") {
    return (
      <div className="border border-border rounded-[14px] bg-card shadow-[0_1px_2px_rgba(10,20,40,.06)] p-4 max-w-[540px]">
        <TypeaheadPicker onSubmit={(v) => onSubmit(v)} disabled={disabled} />
      </div>
    );
  }

  if (askKind === "number") {
    return (
      <div className="flex items-center gap-2 max-w-[320px]">
        <input
          type="number"
          value={numVal}
          onChange={(e) => setNumVal(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && numVal.trim()) onSubmit(numVal.trim());
          }}
          disabled={disabled}
          placeholder="Enter a number"
          className="flex-1 rounded-[10px] border border-border bg-card px-3.5 py-2.5 text-[14px] text-foreground placeholder:text-muted-foreground focus:border-secondary focus:outline-none focus:ring-2 focus:ring-secondary/20 disabled:opacity-50"
        />
        <Button
          variant="secondary"
          size="sm"
          disabled={disabled || !numVal.trim()}
          onClick={() => onSubmit(numVal.trim())}
        >
          Save
        </Button>
      </div>
    );
  }

  if (askKind === "date") {
    return (
      <div className="flex items-center gap-2 max-w-[320px]">
        <input
          type="date"
          value={dateVal}
          onChange={(e) => setDateVal(e.target.value)}
          disabled={disabled}
          className="flex-1 rounded-[10px] border border-border bg-card px-3.5 py-2.5 text-[14px] text-foreground focus:border-secondary focus:outline-none focus:ring-2 focus:ring-secondary/20 disabled:opacity-50"
        />
        <Button
          variant="secondary"
          size="sm"
          disabled={disabled || !dateVal}
          onClick={() => onSubmit(dateVal)}
        >
          Save
        </Button>
      </div>
    );
  }

  if (askKind === "range") {
    return (
      <div className="border border-border rounded-[14px] bg-card shadow-[0_1px_2px_rgba(10,20,40,.06)] p-4 max-w-[420px]">
        <p className="text-[12px] font-semibold text-muted-foreground mb-2">
          Yearly budget (USD)
        </p>
        <div className="flex items-center gap-2 mb-3">
          <input
            type="number"
            value={rangeMin}
            onChange={(e) => setRangeMin(e.target.value)}
            disabled={disabled}
            placeholder="Min"
            className="flex-1 rounded-[10px] border border-border bg-card px-3 py-2 text-[14px] text-foreground placeholder:text-muted-foreground focus:border-secondary focus:outline-none focus:ring-2 focus:ring-secondary/20 disabled:opacity-50"
          />
          <span className="text-muted-foreground text-sm">–</span>
          <input
            type="number"
            value={rangeMax}
            onChange={(e) => setRangeMax(e.target.value)}
            disabled={disabled}
            placeholder="Max"
            className="flex-1 rounded-[10px] border border-border bg-card px-3 py-2 text-[14px] text-foreground placeholder:text-muted-foreground focus:border-secondary focus:outline-none focus:ring-2 focus:ring-secondary/20 disabled:opacity-50"
          />
        </div>
        <div className="flex justify-end">
          <Button
            variant="secondary"
            size="sm"
            disabled={disabled || (!rangeMin && !rangeMax)}
            onClick={() => onSubmit({ min: rangeMin || null, max: rangeMax || null })}
          >
            Set budget
          </Button>
        </div>
      </div>
    );
  }

  // text (and any unknown ask_kind fallback)
  return (
    <div className="flex flex-col gap-2 max-w-[540px]">
      <textarea
        value={textVal}
        onChange={(e) => setTextVal(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter" && !e.shiftKey && textVal.trim()) {
            e.preventDefault();
            onSubmit(textVal.trim());
          }
        }}
        disabled={disabled}
        rows={3}
        placeholder="Type your answer…"
        className="w-full rounded-[10px] border border-border bg-card px-3.5 py-2.5 text-[14px] text-foreground placeholder:text-muted-foreground focus:border-secondary focus:outline-none focus:ring-2 focus:ring-secondary/20 disabled:opacity-50 resize-none"
      />
      <div className="flex justify-end">
        <Button
          variant="secondary"
          size="sm"
          disabled={disabled || !textVal.trim()}
          onClick={() => onSubmit(textVal.trim())}
        >
          Save <ArrowRight size={13} className="ml-1" />
        </Button>
      </div>
    </div>
  );
}

// ── Action artifact cards ─────────────────────────────────────────────────────

/** Renders a single match/comparison row item. */
function SchoolItem({ item }: { item: ActionArtifactItem }) {
  return (
    <div className="flex items-start justify-between gap-3 py-2.5 border-b border-border last:border-0">
      <div className="min-w-0">
        <p className="text-[13.5px] font-semibold text-foreground truncate">{item.name}</p>
        {item.program && (
          <p className="text-[12px] text-muted-foreground truncate">{item.program}</p>
        )}
      </div>
      <div className="flex gap-1.5 shrink-0">
        {item.fit_label && (
          <span className="text-[11px] font-bold px-2 py-0.5 rounded-full bg-secondary/10 text-secondary">
            {item.fit_label}
          </span>
        )}
        {item.odds_label && (
          <span className="text-[11px] font-bold px-2 py-0.5 rounded-full bg-muted text-muted-foreground">
            {item.odds_label}
          </span>
        )}
      </div>
    </div>
  );
}

/** Renders the artifact returned by the action endpoint. */
function ActionArtifactCard({
  artifact,
  onDone,
}: {
  artifact: ActionArtifact;
  onDone: () => void;
}) {
  const navigate = useNavigate();
  const isPending = artifact.status === "pending";

  return (
    <div className="border border-border rounded-[16px] bg-card shadow-[0_1px_2px_rgba(10,20,40,.06)] overflow-hidden max-w-[540px]">
      <div className="flex items-center gap-2.5 px-4 py-3 border-b border-border">
        <span className="text-secondary text-base font-bold" aria-hidden="true">★</span>
        <span className="text-[14.5px] font-bold text-foreground">{artifact.title}</span>
        {isPending && (
          <span className="ml-auto text-[11px] font-semibold text-muted-foreground bg-muted rounded-full px-2.5 py-0.5">
            Coming soon
          </span>
        )}
      </div>
      <div className="px-4 py-4">
        {/* Summary text (strategy narrative, pending message, or no-match note) */}
        {artifact.summary && (
          <p className="text-[13.5px] text-muted-foreground leading-relaxed mb-3">
            {artifact.summary}
          </p>
        )}

        {/* List items for school_list / comparison */}
        {artifact.items && artifact.items.length > 0 && (
          <div className="divide-y divide-border rounded-[10px] border border-border overflow-hidden mb-3">
            {artifact.items.map((item, i) => (
              <SchoolItem key={i} item={item} />
            ))}
          </div>
        )}

        <div className="flex items-center justify-end gap-3">
          {artifact.link && (
            <button
              type="button"
              onClick={() => navigate(artifact.link as string)}
              className="text-[12.5px] font-bold text-secondary hover:text-secondary/80 transition-colors"
            >
              Open in My Space <ArrowRight size={13} className="inline-block ml-0.5 -mt-0.5" />
            </button>
          )}
          <Button variant="secondary" size="sm" onClick={onDone}>
            Continue <ArrowRight size={13} className="ml-1" />
          </Button>
        </div>
      </div>
    </div>
  );
}

// ── Action step — calls endpoint, renders artifact ────────────────────────────

function ActionStep({
  step,
  onDone,
}: {
  step: TemplateStep;
  onDone: () => void;
}) {
  const [artifact, setArtifact] = useState<ActionArtifact | null>(null);
  const [working, setWorking] = useState(true);

  useEffect(() => {
    let cancelled = false;
    const actionKey = step.action_key ?? "";

    dispatchTemplateAction(actionKey)
      .then((result) => {
        if (!cancelled) {
          setArtifact(result);
          setWorking(false);
        }
      })
      .catch(() => {
        if (!cancelled) {
          // Network / server error — show an honest pending card.
          setArtifact({
            action_key: actionKey,
            kind: "note",
            title: step.action_label ?? step.label,
            summary: "This is coming soon — your inputs are saved.",
            status: "pending",
          });
          setWorking(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [step.action_key, step.action_label, step.label]);

  if (working) {
    return (
      <div
        className="inline-flex items-center gap-2 text-[12.5px] font-bold text-muted-foreground bg-muted rounded-full px-3.5 py-2 self-start"
        aria-live="polite"
        aria-label="Uni is working"
      >
        <span
          className="h-1.5 w-1.5 rounded-full bg-primary animate-pulse"
          aria-hidden="true"
        />
        {step.action_label ?? "Working on it"}…
      </div>
    );
  }

  if (!artifact) return null;

  return <ActionArtifactCard artifact={artifact} onDone={onDone} />;
}

// ── Artifact / completion card ────────────────────────────────────────────────

function ArtifactCard({
  template,
  onClose,
}: {
  template: ChatTemplate;
  onClose: () => void;
}) {
  return (
    <div className="border border-border rounded-[16px] bg-card shadow-[0_4px_12px_-4px_rgba(10,20,40,.12)] overflow-hidden max-w-[540px] animate-in fade-in slide-in-from-bottom-2 duration-500">
      <div className="flex items-center gap-2.5 px-4 py-3 border-b border-border">
        <span className="text-secondary text-base font-bold">★</span>
        <span className="text-[14.5px] font-bold text-foreground">{template.outcome}</span>
        <button
          onClick={onClose}
          aria-label="Save to My Space and close"
          className="ml-auto text-[12.5px] font-bold text-secondary hover:text-secondary/80 transition-colors"
        >
          Save to My Space →
        </button>
      </div>
      <div className="px-4 py-4">
        <p className="text-[13.5px] text-muted-foreground leading-relaxed">
          Your answers for{" "}
          <span className="font-semibold text-foreground">{template.title}</span> are
          saved to your profile. They'll sharpen your matches and make future steps
          faster.
        </p>
      </div>
    </div>
  );
}

// ── Uni framing text for each step ───────────────────────────────────────────

function stepFramingText(step: TemplateStep, stepIndex: number): string {
  if (step.question) return step.question;
  if (step.step_type === "action") {
    return `Now Uni will ${(step.action_label ?? step.label).toLowerCase()}.`;
  }
  if (stepIndex === 0) return "Let's get started. First — ";
  return "Next — ";
}

// ── The runner ────────────────────────────────────────────────────────────────

export default function TemplateRunner({ templateKey, onClose }: Props) {
  const [currentStepIndex, setCurrentStepIndex] = useState(0);
  const [completedStepValues, setCompletedStepValues] = useState<
    Array<{ step: TemplateStep; value: unknown }>
  >([]);
  const [saving, setSaving] = useState(false);
  const [done, setDone] = useState(false);

  const { data: templates, isLoading, error } = useQuery({
    queryKey: ["chat-templates"],
    queryFn: getChatTemplates,
    staleTime: 5 * 60_000,
    retry: 1,
  });

  const template = templates?.find((t) => t.key === templateKey) ?? null;
  const steps = template?.steps ?? [];
  const currentStep = steps[currentStepIndex] ?? null;

  const advance = useCallback(() => {
    const next = currentStepIndex + 1;
    if (next >= steps.length) {
      setDone(true);
    } else {
      setCurrentStepIndex(next);
    }
  }, [currentStepIndex, steps.length]);

  const handlePromptSubmit = useCallback(
    async (value: unknown) => {
      if (!currentStep?.prompt_key) return;
      setSaving(true);
      try {
        await setEnrichValue(currentStep.prompt_key, value);
      } catch {
        // Don't block the runner on a write failure — move on.
      } finally {
        setSaving(false);
        setCompletedStepValues((prev) => [...prev, { step: currentStep, value }]);
        advance();
      }
    },
    [currentStep, advance],
  );

  // Loading / error states
  if (isLoading) {
    return (
      <div className="flex-1 flex items-center justify-center text-muted-foreground text-sm">
        Loading…
      </div>
    );
  }

  if (error || !template) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center gap-3 text-center px-6">
        <p className="text-[14px] text-muted-foreground">
          {error ? "Couldn't load the template." : `Template "${templateKey}" not found.`}
        </p>
        <Button variant="ghost" size="sm" onClick={onClose}>
          Go back
        </Button>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col min-h-0 overflow-hidden">
      {/* ── Top bar ── */}
      <div className="border-b border-border bg-card shrink-0">
        <div className="max-w-[700px] mx-auto px-6 pt-4 pb-2 flex items-center gap-2.5">
          <div className="w-[30px] h-[30px] rounded-[9px] bg-secondary/10 text-secondary flex items-center justify-center shrink-0">
            <TemplateIcon icon={template.icon} size={18} />
          </div>
          <span className="text-[15px] font-bold text-foreground truncate">{template.title}</span>
          {!done && (
            <span className="ml-auto text-[12.5px] font-semibold text-muted-foreground shrink-0">
              Step {currentStepIndex + 1} of {steps.length}
            </span>
          )}
          {/* Close / exit */}
          <button
            onClick={onClose}
            aria-label="Exit this session"
            className="ml-2 w-7 h-7 rounded-full flex items-center justify-center text-muted-foreground hover:bg-muted hover:text-foreground transition-colors shrink-0"
          >
            <X size={14} />
          </button>
        </div>

        {/* Work-order spine */}
        <Spine steps={steps} currentIndex={done ? steps.length : currentStepIndex} />
      </div>

      {/* ── Conversation scroll ── */}
      <div className="flex-1 overflow-y-auto min-h-0">
        <div
          className="max-w-[700px] mx-auto px-6 py-6 flex flex-col gap-5"
          aria-live="polite"
          aria-label="Conversation"
        >
          {/* Past completed steps — brief confirmation */}
          {completedStepValues.map(({ step }, idx) => (
            <div key={idx} className="flex justify-end animate-in fade-in duration-300">
              <div className="bg-secondary/10 border border-secondary/20 rounded-[14px] rounded-br-[5px] px-4 py-2.5 text-[14.5px] text-foreground max-w-[75%]">
                {step.label} — saved
              </div>
            </div>
          ))}

          {/* Current step — or completion card */}
          {done ? (
            <UniTurn>
              <p className="text-[15.5px] leading-relaxed">
                You're done. Here's what we built together.
              </p>
              <ArtifactCard template={template} onClose={onClose} />
            </UniTurn>
          ) : currentStep ? (
            <UniTurn>
              {/* Framing text */}
              <p className="text-[15.5px] leading-relaxed">
                {stepFramingText(currentStep, currentStepIndex)}
              </p>

              {/* Widget or action */}
              {currentStep.step_type === "prompt" ? (
                <PromptStepWidget
                  step={currentStep}
                  onSubmit={handlePromptSubmit}
                  disabled={saving}
                />
              ) : (
                <ActionStep step={currentStep} onDone={advance} />
              )}
            </UniTurn>
          ) : null}
        </div>
      </div>
    </div>
  );
}
