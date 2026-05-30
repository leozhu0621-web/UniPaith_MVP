// Breadcrumbs — Spec/02-design-system.md §7.
// On every detail page (program, school, application, student record).
// Middle-dot `·` separators in --text-mut. Last item not a link.
//
//   Discover · Search results · Computer Science MS · ◾ University of Foo

import { Link } from 'react-router-dom'
import clsx from 'clsx'

export type Crumb = {
  label: string
  /** Internal `to` path. Omit for the last (current page). */
  to?: string
  /** Render with a leading square mark — used for the current institution
   *  context in detail breadcrumbs (Spec §7). */
  mark?: boolean
}

interface BreadcrumbsProps {
  items: Crumb[]
  className?: string
}

export default function Breadcrumbs({ items, className }: BreadcrumbsProps) {
  return (
    <nav aria-label="Breadcrumb" className={clsx('text-[13px]', className)}>
      <ol className="flex flex-wrap items-center gap-x-1.5 gap-y-1">
        {items.map((item, i) => {
          const isLast = i === items.length - 1
          return (
            <li key={`${item.label}-${i}`} className="inline-flex items-center gap-1.5">
              {item.mark && (
                <span aria-hidden="true" className="inline-block w-2 h-2 rounded-sm bg-[#FFD60A] dark:bg-[#F2C800]" />
              )}
              {isLast || !item.to ? (
                <span aria-current={isLast ? 'page' : undefined} className="text-foreground font-bold">
                  {item.label}
                </span>
              ) : (
                <Link
                  to={item.to}
                  className="text-muted-foreground hover:text-foreground hover:underline underline-offset-2 motion-fast transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#FFD60A] rounded-sm"
                >
                  {item.label}
                </Link>
              )}
              {!isLast && (
                <span aria-hidden="true" className="text-muted-foreground">
                  ·
                </span>
              )}
            </li>
          )
        })}
      </ol>
    </nav>
  )
}
