import Button from './Button'
import { COPY } from '../../lib/copy'

// Empty state — Spec/02-design-system.md §12. No illustrations, no marketing
// tone. The body explains what would put data here.
interface EmptyStateProps {
  icon?: React.ReactNode
  title?: string
  description?: string
  action?: { label: string; onClick: () => void }
}

export default function EmptyState({ icon, title = COPY.emptyGeneric, description, action }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center" role="status" aria-live="polite">
      {icon && (
        <div className="mb-4 text-muted-foreground" aria-hidden="true">
          {icon}
        </div>
      )}
      <h3 className="text-h3 text-foreground">{title}</h3>
      {description && <p className="mt-1.5 text-sm text-muted-foreground max-w-[56ch]">{description}</p>}
      {action && (
        <Button onClick={action.onClick} variant="secondary" className="mt-5">
          {action.label}
        </Button>
      )}
    </div>
  )
}
