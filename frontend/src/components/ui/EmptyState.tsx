// EmptyState — Spec/02-design-system.md §12.
// Whenever a list, dashboard, or workspace has no data.
// No illustrations, no marketing tone. The body sentence explains
// *what would put data here*. Brand-tokened, sentence-case.

import Button from './Button'
import clsx from 'clsx'

interface EmptyStateProps {
  icon?: React.ReactNode
  title: string
  description?: string
  action?: { label: string; onClick: () => void }
  secondaryAction?: { label: string; onClick: () => void }
  className?: string
}

export default function EmptyState({
  icon,
  title,
  description,
  action,
  secondaryAction,
  className,
}: EmptyStateProps) {
  return (
    <div
      className={clsx(
        'flex flex-col items-center justify-center py-16 px-6 text-center',
        className,
      )}
    >
      {icon && (
        <div className="mb-4 text-muted-foreground flex items-center justify-center">
          {icon}
        </div>
      )}
      <h3 className="text-[20px] leading-[1.3] font-bold text-foreground">{title}</h3>
      {description && (
        <p className="mt-2 text-base text-muted-foreground max-w-[56ch] leading-[1.6]">
          {description}
        </p>
      )}
      {(action || secondaryAction) && (
        <div className="mt-6 flex items-center gap-2">
          {secondaryAction && (
            <Button variant="tertiary" onClick={secondaryAction.onClick}>
              {secondaryAction.label}
            </Button>
          )}
          {action && (
            <Button variant="secondary" onClick={action.onClick}>
              {action.label}
            </Button>
          )}
        </div>
      )}
    </div>
  )
}
