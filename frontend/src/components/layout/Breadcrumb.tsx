import { Link } from 'react-router-dom'

export interface Crumb {
  label: string
  to?: string
}

interface BreadcrumbProps {
  items: (Crumb | null | undefined | false)[]
  className?: string
}

// Drill-down breadcrumb — Spec/04 §7.5.
// Middle-dot (·) separators, muted color, last item is plain text (not a link).
// Shared by student and institution drill-down pages (§15 compliance checklist).
export default function Breadcrumb({ items, className = '' }: BreadcrumbProps) {
  const visible = items.filter(Boolean) as Crumb[]
  if (visible.length === 0) return null

  return (
    <nav
      aria-label="Breadcrumb"
      className={`flex items-center flex-wrap gap-x-1.5 gap-y-0.5 text-xs text-slate ${className}`}
    >
      {visible.map((item, i) => {
        const isLast = i === visible.length - 1
        const isLink = !!item.to && !isLast
        return (
          <span key={`${item.label}-${i}`} className="flex items-center gap-x-1.5 min-w-0">
            {i > 0 && (
              <span aria-hidden className="text-stone select-none">
                ·
              </span>
            )}
            {isLink ? (
              <Link
                to={item.to!}
                className="truncate max-w-[14rem] hover:text-student-ink hover:underline transition-colors"
              >
                {item.label}
              </Link>
            ) : (
              <span
                aria-current={isLast ? 'page' : undefined}
                className={
                  isLast
                    ? 'truncate max-w-[20rem] text-student-ink font-medium'
                    : 'truncate max-w-[14rem]'
                }
              >
                {item.label}
              </span>
            )}
          </span>
        )
      })}
    </nav>
  )
}
