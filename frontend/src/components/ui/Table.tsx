import { useState } from 'react'
import clsx from 'clsx'
import { ChevronDown, ChevronUp, ChevronsUpDown } from 'lucide-react'
import Skeleton from './Skeleton'

// Table — Spec/02-design-system.md §8 + Spec 79. Muted sticky header with eyebrow
// labels; alternating rows; muted hover; 12y/16x cell padding. Columns can opt in
// to client-side sorting (sortable) — keyboard-operable header + aria-sort.
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
  // Optional per-row class (e.g. tint override events). Applied last so it
  // can override the alternating-row background.
  rowClassName?: (row: any) => string | undefined
}

type SortState = { key: string; dir: 'asc' | 'desc' } | null

export default function Table({ columns, data, onRowClick, isLoading, emptyMessage = 'No records match', rowClassName }: TableProps) {
  const [sort, setSort] = useState<SortState>(null)

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

  const cycleSort = (key: string) =>
    setSort(prev =>
      prev?.key !== key ? { key, dir: 'asc' } : prev.dir === 'asc' ? { key, dir: 'desc' } : null,
    )

  return (
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
          {sorted.map((row, i) => (
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
  )
}
