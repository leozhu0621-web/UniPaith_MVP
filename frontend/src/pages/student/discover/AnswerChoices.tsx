/**
 * Tap-to-answer choice cards for the Uni conversation.
 *
 * Renders the orchestrator's `suggested_options` as warm, single-tap answer
 * cards (an upgrade of the old muted pill chips) so a turn feels interactive,
 * not just a text box. Tapping a card sends it as the student's reply. Typing is
 * always still available below. Phase 2 extends this with multi-select + a 1–5
 * importance slider driven by an additive `suggested_input` hint.
 */
import clsx from 'clsx'
import { Plus } from 'lucide-react'

export default function AnswerChoices({
  options,
  onPick,
  disabled = false,
}: {
  options: string[]
  onPick: (value: string) => void
  disabled?: boolean
}) {
  if (options.length === 0) return null
  return (
    <div className="mb-2 grid gap-1.5 sm:grid-cols-2 stagger-list" role="group" aria-label="Suggested answers">
      {options.map(opt => (
        <button
          key={opt}
          type="button"
          disabled={disabled}
          onClick={() => onPick(opt)}
          className={clsx(
            'group flex items-center gap-2 rounded-lg border border-border bg-card px-3 py-2 text-left text-sm text-foreground',
            'transition-all duration-150 ease-out',
            'motion-safe:hover:-translate-y-px hover:border-secondary/50 hover:bg-secondary/5',
            'focus:outline-none focus-visible:ring-2 focus-visible:ring-secondary/40',
            'disabled:opacity-50 disabled:pointer-events-none',
          )}
        >
          <span className="text-secondary/60 transition-colors group-hover:text-secondary shrink-0">
            <Plus size={14} />
          </span>
          <span className="flex-1">{opt}</span>
        </button>
      ))}
    </div>
  )
}
