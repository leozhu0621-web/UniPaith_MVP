import clsx from 'clsx'
import { ChevronLeft, ChevronRight } from 'lucide-react'

/**
 * Pagination — numbered page control with ellipsis (UX-QA: browsing in pages,
 * not a load-more). Current page is cobalt; ends collapse to "1 … 5 6 7 … 20".
 * Returns null for a single page. The page-change side effects (scroll-to-top)
 * live with the caller.
 */
interface PaginationProps {
  page: number
  pageCount: number
  onChange: (page: number) => void
  className?: string
}

/** Pages to render: all of them when few, else first/last + a window around the
 *  current page, with 'gap' markers for the elided runs. */
function buildPages(page: number, pageCount: number): (number | 'gap')[] {
  if (pageCount <= 7) return Array.from({ length: pageCount }, (_, i) => i + 1)
  const out: (number | 'gap')[] = [1]
  const start = Math.max(2, page - 1)
  const end = Math.min(pageCount - 1, page + 1)
  if (start > 2) out.push('gap')
  for (let p = start; p <= end; p++) out.push(p)
  if (end < pageCount - 1) out.push('gap')
  out.push(pageCount)
  return out
}

const CELL = 'inline-flex h-9 min-w-9 items-center justify-center rounded-md px-2 text-sm transition-colors'
const NAV = clsx(
  CELL,
  'text-muted-foreground hover:bg-muted hover:text-foreground',
  'disabled:pointer-events-none disabled:opacity-40',
)

export default function Pagination({ page, pageCount, onChange, className }: PaginationProps) {
  if (pageCount <= 1) return null
  return (
    <nav aria-label="Pagination" className={clsx('flex items-center justify-center gap-1', className)}>
      <button type="button" aria-label="Previous page" disabled={page <= 1} onClick={() => onChange(page - 1)} className={NAV}>
        <ChevronLeft size={16} aria-hidden="true" />
      </button>
      {buildPages(page, pageCount).map((p, i) =>
        p === 'gap' ? (
          <span key={`gap-${i}`} className="px-1 text-muted-foreground select-none" aria-hidden="true">…</span>
        ) : (
          <button
            key={p}
            type="button"
            aria-label={`Page ${p}`}
            aria-current={p === page ? 'page' : undefined}
            onClick={() => onChange(p)}
            className={clsx(
              CELL,
              p === page
                ? 'bg-secondary font-semibold text-secondary-foreground'
                : 'text-foreground hover:bg-muted',
            )}
          >
            {p}
          </button>
        ),
      )}
      <button type="button" aria-label="Next page" disabled={page >= pageCount} onClick={() => onChange(page + 1)} className={NAV}>
        <ChevronRight size={16} aria-hidden="true" />
      </button>
    </nav>
  )
}
