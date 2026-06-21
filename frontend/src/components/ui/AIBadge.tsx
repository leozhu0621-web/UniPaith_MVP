import { Sparkles } from 'lucide-react'
import clsx from 'clsx'
import Tooltip from './Tooltip'

// Spec 02 §15 — visible AI attribution. A small "AI assist" badge with an
// accent (cobalt) outline on a surface background. Use on every UI region that
// surfaces AI-generated content. When `fallback` is set (the agent fell back to
// the rule-based path), the badge says so plainly (§15.5).
interface AIBadgeProps {
  label?: string
  fallback?: boolean
  className?: string
}

export default function AIBadge({ label = 'AI assist', fallback = false, className }: AIBadgeProps) {
  const tooltip = fallback
    ? 'Shown from the rule-based fallback because the AI path was unavailable.'
    : 'AI helped prepare this content. Review important details before acting.'

  return (
    <Tooltip content={tooltip}>
      <span
        className={clsx(
          'inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-xs font-medium',
          fallback
            ? 'border-warning/40 bg-warning-soft text-warning'
            : 'border-secondary/30 bg-secondary/5 text-secondary',
          className,
        )}
      >
        <Sparkles size={11} className="shrink-0" aria-hidden="true" />
        {fallback ? 'Rule-based' : label}
      </span>
    </Tooltip>
  )
}
