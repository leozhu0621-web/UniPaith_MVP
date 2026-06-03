import clsx from 'clsx'
import { X } from 'lucide-react'

// Constraint chip — Spec/02-design-system.md §9 (Discovery critical pattern).
// Pill, 1px cobalt border, surface bg. Label "Category · Value". Trailing ✕
// removes; clicking the label opens an in-place editor for that field.

interface ConstraintChipProps {
  category: string
  value: string
  onRemove?: () => void
  onEdit?: () => void
  className?: string
}

export default function ConstraintChip({ category, value, onRemove, onEdit, className }: ConstraintChipProps) {
  return (
    <span
      className={clsx(
        'inline-flex items-center rounded-pill border border-secondary bg-card text-foreground text-[13px] h-8 overflow-hidden',
        className
      )}
    >
      <button
        type="button"
        onClick={onEdit}
        disabled={!onEdit}
        className={clsx(
          'inline-flex items-center gap-1 pl-3 pr-2 h-full',
          onEdit && 'hover:bg-muted transition-colors cursor-pointer'
        )}
      >
        <span className="text-muted-foreground">{category}</span>
        <span className="text-muted-foreground" aria-hidden="true">·</span>
        <span className="font-semibold">{value}</span>
      </button>
      {onRemove && (
        <button
          type="button"
          onClick={onRemove}
          aria-label={`Remove ${category} ${value}`}
          className="inline-flex items-center justify-center w-8 h-full text-muted-foreground hover:bg-muted hover:text-error transition-colors border-l border-secondary/40"
        >
          <X size={14} />
        </button>
      )}
    </span>
  )
}
