/**
 * Tap-to-answer affordances for the Uni conversation and the enrich widgets.
 *
 * The widget language locked in the 2026-06-19 widget-library design:
 *   - 'choice' (default): option cards — whole card tappable, trailing
 *     checkmark; one tap sends that answer.
 *   - 'multi': option cards with a clean checkbox + a Continue that sends the
 *     joined picks.
 *   - 'scale': a tap-meter (five segments + a plain word), not a drag slider —
 *     for "how important" / 0–5 importance questions.
 * Typing stays available wherever this is used. Shared by the conversation
 * (`suggested_options`) and `EnrichWidget`; brand tokens (secondary = cobalt).
 */
import { useState } from 'react'
import clsx from 'clsx'
import { ArrowRight, Check } from 'lucide-react'

import Button from '../../../components/ui/Button'

export type AnswerKind = 'choice' | 'multi' | 'scale'

const CARD =
  'group flex items-center gap-2.5 rounded-xl border-[1.5px] border-border bg-card px-3.5 py-3 text-left text-sm font-medium text-foreground transition-all duration-150 ease-out min-h-[2.75rem] motion-safe:hover:-translate-y-px hover:border-secondary/60 hover:shadow-sm focus:outline-none focus-visible:ring-2 focus-visible:ring-secondary/40 disabled:opacity-50 disabled:pointer-events-none'

function ChoiceCards({
  options,
  onPick,
  disabled,
}: {
  options: string[]
  onPick: (v: string) => void
  disabled?: boolean
}) {
  return (
    <div className="mb-2 grid gap-2 sm:grid-cols-2 stagger-list" role="group" aria-label="Suggested answers">
      {options.map(opt => (
        <button key={opt} type="button" disabled={disabled} onClick={() => onPick(opt)} className={CARD}>
          <span className="flex-1">{opt}</span>
          <Check
            size={16}
            className="shrink-0 text-secondary opacity-0 transition-opacity group-hover:opacity-100"
          />
        </button>
      ))}
    </div>
  )
}

function MultiSelect({
  options,
  onPick,
  disabled,
  asList,
}: {
  options: string[]
  onPick: (v: string | string[]) => void
  disabled?: boolean
  /** When true, submits an array of selected strings instead of a joined phrase.
   *  Used by EnrichWidget so the backend receives a proper list. The conversation
   *  path (no asList) keeps the natural-language joined string. */
  asList?: boolean
}) {
  const [sel, setSel] = useState<string[]>([])
  const toggle = (o: string) => setSel(s => (s.includes(o) ? s.filter(x => x !== o) : [...s, o]))
  const send = () => {
    if (sel.length === 0) return
    if (asList) {
      onPick(sel)
      return
    }
    const joined =
      sel.length === 1 ? sel[0] : `${sel.slice(0, -1).join(', ')} and ${sel[sel.length - 1]}`
    onPick(joined)
  }
  return (
    <div className="mb-2">
      <div className="grid gap-2 sm:grid-cols-2 stagger-list" role="group" aria-label="Pick any that fit">
        {options.map(opt => {
          const on = sel.includes(opt)
          return (
            <button
              key={opt}
              type="button"
              disabled={disabled}
              aria-pressed={on}
              onClick={() => toggle(opt)}
              className={clsx(CARD, on && '!border-secondary !bg-secondary/10')}
            >
              <span
                className={clsx(
                  'flex h-[1.3rem] w-[1.3rem] shrink-0 items-center justify-center rounded-md border-[1.5px] transition-colors',
                  on ? 'border-secondary bg-secondary text-secondary-foreground' : 'border-border',
                )}
              >
                {on && <Check size={13} strokeWidth={3} />}
              </span>
              <span className="flex-1">{opt}</span>
            </button>
          )
        })}
      </div>
      <div className="mt-2 flex items-center justify-end gap-2.5">
        <span className="text-xs text-muted-foreground">
          {sel.length ? `${sel.length} picked` : 'pick any that fit'}
        </span>
        <Button variant="secondary" size="sm" disabled={disabled || sel.length === 0} onClick={send}>
          Continue <ArrowRight size={14} className="ml-1" />
        </Button>
      </div>
    </div>
  )
}

function Scale({
  onPick,
  disabled,
  lowLabel,
  highLabel,
  numeric,
}: {
  onPick: (v: string) => void
  disabled?: boolean
  lowLabel?: string
  highLabel?: string
  // Enrichment fields need the raw 0–5 number (the backend scales it 0–10 onto
  // StudentPreference); the conversational path keeps the natural-language phrase.
  numeric?: boolean
}) {
  const [v, setV] = useState(3)
  const low = lowLabel || 'not important'
  const high = highLabel || 'essential'
  const phrase = (() => {
    if (v <= 1) return low
    if (v >= 5) return high
    if (v === 2) return `more ${low.toLowerCase()} than not`
    if (v === 4) return `more ${high.toLowerCase()} than not`
    return 'somewhere in the middle'
  })()
  return (
    <div className="mb-2 rounded-xl border-[1.5px] border-border bg-card px-3.5 py-3">
      <div className="flex gap-1.5" role="group" aria-label="How important is this to you, from 1 to 5">
        {[1, 2, 3, 4, 5].map(n => (
          <button
            key={n}
            type="button"
            disabled={disabled}
            aria-label={`Set importance to ${n}`}
            aria-pressed={n === v}
            onClick={() => setV(n)}
            className={clsx(
              'h-8 flex-1 rounded-md transition-colors duration-150 motion-safe:hover:-translate-y-px',
              n <= v ? 'bg-secondary' : 'bg-muted hover:bg-muted/70',
            )}
          />
        ))}
      </div>
      <div className="mt-2.5 flex items-center justify-between">
        <span className="text-xs font-medium text-secondary">{phrase}</span>
        <Button
          variant="secondary"
          size="sm"
          disabled={disabled}
          onClick={() => onPick(numeric ? String(v) : phrase)}
        >
          Set
        </Button>
      </div>
    </div>
  )
}

export default function AnswerChoices({
  options,
  onPick,
  disabled = false,
  kind = 'choice',
  lowLabel,
  highLabel,
  numeric = false,
  asList = false,
}: {
  options: string[]
  onPick: (value: string | string[]) => void
  disabled?: boolean
  kind?: AnswerKind
  lowLabel?: string
  highLabel?: string
  numeric?: boolean
  /** multi only: submit a string[] instead of the joined phrase (for EnrichWidget). */
  asList?: boolean
}) {
  if (kind === 'scale') {
    return (
      <Scale
        onPick={onPick as (v: string) => void}
        disabled={disabled}
        lowLabel={lowLabel}
        highLabel={highLabel}
        numeric={numeric}
      />
    )
  }
  if (options.length === 0) return null
  if (kind === 'multi') {
    return <MultiSelect options={options} onPick={onPick} disabled={disabled} asList={asList} />
  }
  return <ChoiceCards options={options} onPick={onPick as (v: string) => void} disabled={disabled} />
}
