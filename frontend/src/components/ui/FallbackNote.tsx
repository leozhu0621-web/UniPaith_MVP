import { Info } from 'lucide-react'
import clsx from 'clsx'

// Spec 02 §15.5 / 37 §1.3 — the single, canonical "Showing rule-based result"
// note shown whenever an AI agent fell back to its deterministic path. Use this
// instead of hand-rolling the string so every AI surface reads the same.
interface FallbackNoteProps {
  /** Override the default copy when a surface needs more specific wording. */
  children?: React.ReactNode
  className?: string
}

export default function FallbackNote({ children, className }: FallbackNoteProps) {
  return (
    <p className={clsx('flex items-center gap-1.5 text-xs italic text-muted-foreground', className)}>
      <Info size={12} className="shrink-0" />
      {children ?? 'Showing rule-based result.'}
    </p>
  )
}
