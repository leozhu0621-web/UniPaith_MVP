/**
 * Tap-to-answer affordances for the Uni conversation.
 *
 * Renders the orchestrator's `suggested_options` as warm answer surfaces so a
 * turn feels interactive, not just a text box. The optional `suggested_input`
 * hint (Phase 2) picks the shape:
 *   - 'choice' (default): single-tap cards — one tap sends that answer.
 *   - 'multi': multi-select cards + a Continue that sends the joined picks.
 *   - 'scale': a 1–5 importance slider (for needs / "how important" questions).
 * Typing is always available below regardless.
 */
import { useState } from 'react'
import clsx from 'clsx'
import { ArrowRight, Check, Plus } from 'lucide-react'

import Button from '../../../components/ui/Button'

export type AnswerKind = 'choice' | 'multi' | 'scale'

const CARD =
  'group flex items-center gap-2 rounded-lg border border-border bg-card px-3 py-2 text-left text-sm text-foreground transition-all duration-150 ease-out motion-safe:hover:-translate-y-px hover:border-secondary/50 hover:bg-secondary/5 focus:outline-none focus-visible:ring-2 focus-visible:ring-secondary/40 disabled:opacity-50 disabled:pointer-events-none'

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
    <div className="mb-2 grid gap-1.5 sm:grid-cols-2 stagger-list" role="group" aria-label="Suggested answers">
      {options.map(opt => (
        <button key={opt} type="button" disabled={disabled} onClick={() => onPick(opt)} className={CARD}>
          <span className="text-secondary/60 transition-colors group-hover:text-secondary shrink-0">
            <Plus size={14} />
          </span>
          <span className="flex-1">{opt}</span>
        </button>
      ))}
    </div>
  )
}

function MultiSelect({
  options,
  onPick,
  disabled,
}: {
  options: string[]
  onPick: (v: string) => void
  disabled?: boolean
}) {
  const [sel, setSel] = useState<string[]>([])
  const toggle = (o: string) => setSel(s => (s.includes(o) ? s.filter(x => x !== o) : [...s, o]))
  const send = () => {
    if (sel.length === 0) return
    const joined =
      sel.length === 1 ? sel[0] : `${sel.slice(0, -1).join(', ')} and ${sel[sel.length - 1]}`
    onPick(joined)
  }
  return (
    <div className="mb-2">
      <div className="grid gap-1.5 sm:grid-cols-2 stagger-list" role="group" aria-label="Pick any that fit">
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
              <span className={clsx('shrink-0', on ? 'text-secondary' : 'text-secondary/60')}>
                {on ? <Check size={14} /> : <Plus size={14} />}
              </span>
              <span className="flex-1">{opt}</span>
            </button>
          )
        })}
      </div>
      <div className="mt-1.5 flex items-center justify-end gap-2.5">
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
    <div className="mb-2 rounded-lg border border-border bg-card px-3.5 py-3">
      <div className="flex items-center gap-3">
        <span className="text-xs text-muted-foreground shrink-0">{low}</span>
        <input
          type="range"
          min={1}
          max={5}
          step={1}
          value={v}
          disabled={disabled}
          onChange={e => setV(Number(e.target.value))}
          className="flex-1"
          style={{ accentColor: 'hsl(var(--secondary))' }}
          aria-label="How important is this to you, from 1 to 5"
        />
        <span className="text-xs text-muted-foreground shrink-0">{high}</span>
      </div>
      <div className="mt-2 flex items-center justify-between">
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
}: {
  options: string[]
  onPick: (value: string) => void
  disabled?: boolean
  kind?: AnswerKind
  lowLabel?: string
  highLabel?: string
  numeric?: boolean
}) {
  if (kind === 'scale') {
    return (
      <Scale
        onPick={onPick}
        disabled={disabled}
        lowLabel={lowLabel}
        highLabel={highLabel}
        numeric={numeric}
      />
    )
  }
  if (options.length === 0) return null
  if (kind === 'multi') {
    return <MultiSelect options={options} onPick={onPick} disabled={disabled} />
  }
  return <ChoiceCards options={options} onPick={onPick} disabled={disabled} />
}
