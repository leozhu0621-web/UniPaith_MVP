import { Link } from 'react-router-dom'
import clsx from 'clsx'

// Breadcrumbs — Spec/02-design-system.md §7. Middle-dot separators, muted color;
// the last item is the current page (not a link).
export interface Crumb {
  label: string
  to?: string
}

export default function Breadcrumbs({ items, className }: { items: Crumb[]; className?: string }) {
  return (
    <nav aria-label="Breadcrumb" className={clsx('flex items-center flex-wrap gap-x-2 gap-y-1 text-sm', className)}>
      {items.map((crumb, i) => {
        const last = i === items.length - 1
        return (
          <span key={`${crumb.label}-${i}`} className="inline-flex items-center gap-2 min-w-0">
            {crumb.to && !last ? (
              <Link to={crumb.to} className="text-muted-foreground hover:text-foreground transition-colors truncate">
                {crumb.label}
              </Link>
            ) : (
              <span className={clsx('truncate', last ? 'text-foreground font-semibold' : 'text-muted-foreground')} aria-current={last ? 'page' : undefined}>
                {crumb.label}
              </span>
            )}
            {!last && <span className="text-stone" aria-hidden="true">·</span>}
          </span>
        )
      })}
    </nav>
  )
}
