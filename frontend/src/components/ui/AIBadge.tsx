import { Sparkles } from 'lucide-react'
import clsx from 'clsx'

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
  return (
    <span
      className={clsx(
        'inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-xs font-medium',
        fallback
          ? 'border-warning/40 bg-warning-soft text-warning'
          : 'border-cobalt/30 bg-cobalt/5 text-cobalt',
        className,
      )}
    >
      <Sparkles size={11} className="shrink-0" />
      {fallback ? 'Rule-based' : label}
    </span>
  )
}
