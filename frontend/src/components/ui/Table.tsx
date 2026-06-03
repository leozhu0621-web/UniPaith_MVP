import { useState } from 'react'
import clsx from 'clsx'
import { ChevronDown, ChevronUp, ChevronsUpDown } from 'lucide-react'
import Skeleton from './Skeleton'

// Table — Spec/02-design-system.md §8 + Spec 79. Muted sticky header with eyebrow
// labels; alternating rows; muted hover; 12y/16x cell padding. Columns can opt in
// to client-side sorting (`sortable`); the table can opt in to client-side
// pagination (`pageSize`). Both are backward-compatible no-ops when unset.
interface Column {
  key: string
  label: string
  render?: (row: any) => React.ReactNode
  align?: 'left' | 'right'
  numeric?: boolean
  /** Opt-in sortable header (Spec 79). Sorts by `sortAccessor` ?? `row[key]`. */
  sortable?: boolean
  sortAccessor?: (row: any) => string | number | null | undefined
}

interface TableProps {
  columns: Column[]
  data: any[]
  onRowClick?: (row: any) => void
  isLoading?: boolean
  emptyMessage?: string
  /** Opt-in client-side pagination (Spec 79). Renders a pager when total > pageSize. */
  pageSize?: number
  // Optional per-row class (e.g. tint override events). Applied last so it
  // can override the alternating-row background.
  rowClassName?: (row: any) => string | undefined
}

type SortState = { key: string; dir: 'asc' | 'desc' } | null

export default function Table({ columns, data, onRowClick, isLoading, emptyMessage = 'No records match', pageSize, rowClassName }: TableProps) {
  const [sort, setSort] = useState<SortState>(null)
  const [page, setPage] = useState(0)

  if (isLoading) {
    return (
      <div className="space-y-2">
        {Array.from({ length: 5 }).map((_, i) => (
          <Skeleton key={i} className="h-12 w-full" />
        ))}
      </div>
    )
  }

  if (data.length === 0) {
    return <div className="text-center py-12 text-sm text-muted-foreground">{emptyMessage}</div>
  }

  const sortCol = sort ? columns.find(c => c.key === sort.key) : undefined
  const sorted = sortCol
    ? [...data].sort((a, b) => {
        const acc = sortCol.sortAccessor ?? ((r: any) => r[sortCol.key])
        const av = acc(a)
        const bv = acc(b)
        if (av == null && bv == null) return 0
        if (av == null) return 1
        if (bv == null) return -1
        const cmp =
          typeof av === 'number' && typeof bv === 'number'
            ? av - bv
            : String(av).localeCompare(String(bv), undefined, { numeric: true })
        return sort!.dir === 'asc' ? cmp : -cmp
      })
    : data

  const total = sorted.length
  const pageCount = pageSize ? Math.max(1, Math.ceil(total / pageSize)) : 1
  const safePage = Math.min(page, pageCount - 1)
  const paged = pageSize ? sorted.slice(safePage * pageSize, safePage * pageSize + pageSize) : sorted

  const cycleSort = (key: string) => {
    setPage(0)
    setSort(prev =>
      prev?.key !== key ? { key, dir: 'asc' } : prev.dir === 'asc' ? { key, dir: 'desc' } : null,
    )
  }

  return (
    <div>
      <div className="overflow-x-auto rounded-lg border border-border">
        <table className="w-full text-sm">
          <thead className="sticky top-0 z-10">
            <tr className="bg-muted">
              {columns.map(col => {
                const isSorted = sort?.key === col.key
                const alignRight = col.align === 'right' || col.numeric
                return (
                  <th
                    key={col.key}
                    aria-sort={isSorted ? (sort!.dir === 'asc' ? 'ascending' : 'descending') : undefined}
                    className={clsx(
                      'px-4 py-3 text-[11px] font-semibold uppercase tracking-wider text-muted-foreground',
                      alignRight ? 'text-right' : 'text-left',
                    )}
                  >
                    {col.sortable ? (
                      <button
                        type="button"
                        onClick={() => cycleSort(col.key)}
                        className={clsx(
                          'inline-flex items-center gap-1 hover:text-foreground transition-colors',
                          alignRight && 'flex-row-reverse',
                          isSorted && 'text-foreground',
                        )}
                      >
                        {col.label}
                        {isSorted ? (
                          sort!.dir === 'asc' ? <ChevronUp size={12} /> : <ChevronDown size={12} />
                        ) : (
                          <ChevronsUpDown size={12} className="opacity-40" />
                        )}
                      </button>
                    ) : (
                      col.label
                    )}
                  </th>
                )
              })}
            </tr>
          </thead>
          <tbody>
            {paged.map((row, i) => (
              <tr
                key={row.id || i}
                onClick={() => onRowClick?.(row)}
                className={clsx(
                  'border-t border-border',
                  i % 2 === 1 && 'bg-muted/30',
                  onRowClick && 'cursor-pointer hover:bg-muted transition-colors',
                  rowClassName?.(row),
                )}
              >
                {columns.map(col => (
                  <td
                    key={col.key}
                    className={clsx(
                      'px-4 py-3 text-foreground',
                      (col.align === 'right' || col.numeric) && 'text-right tabular-nums',
                    )}
                  >
                    {col.render ? col.render(row) : row[col.key]}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {pageSize != null && total > pageSize && (
        <div className="flex items-center justify-between px-1 pt-3 text-xs text-muted-foreground">
          <span>
            {safePage * pageSize + 1}–{Math.min((safePage + 1) * pageSize, total)} of {total}
          </span>
          <div className="flex items-center gap-1">
            <button
              type="button"
              disabled={safePage === 0}
              onClick={() => setPage(safePage - 1)}
              className="rounded-md border border-border px-2.5 py-1 font-medium hover:bg-muted disabled:pointer-events-none disabled:opacity-40"
            >
              Prev
            </button>
            <button
              type="button"
              disabled={safePage >= pageCount - 1}
              onClick={() => setPage(safePage + 1)}
              className="rounded-md border border-border px-2.5 py-1 font-medium hover:bg-muted disabled:pointer-events-none disabled:opacity-40"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
