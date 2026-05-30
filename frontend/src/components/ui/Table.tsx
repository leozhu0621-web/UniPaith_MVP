// Table — Spec/02-design-system.md §8.
// Header row: --muted bg, sticky on scroll, eyebrow-style labels
// (12px / 700 / uppercase). Body rows alternate surface / subtle warm
// wash. Hover: row gets --muted bg. Cell padding 12px y, 16px x.
// Numeric columns right-aligned with tabular-nums.

import clsx from 'clsx'
import { ChevronUp, ChevronDown } from 'lucide-react'
import Skeleton from './Skeleton'

export interface Column<T = Record<string, unknown>> {
  key: string
  label: string
  /** Right-align + tabular-nums. */
  numeric?: boolean
  /** Show sort chevron + accept sort clicks. */
  sortable?: boolean
  render?: (row: T) => React.ReactNode
  /** Column width override (CSS). */
  width?: string
}

type SortDir = 'asc' | 'desc' | null

interface TableProps<T = Record<string, unknown>> {
  columns: Column<T>[]
  data: T[]
  onRowClick?: (row: T) => void
  isLoading?: boolean
  emptyMessage?: string
  emptyAction?: { label: string; onClick: () => void }
  /** Currently sorted column key + direction. */
  sortKey?: string
  sortDir?: SortDir
  onSort?: (key: string) => void
  /** Reserve a 40px-wide leftmost selection cell (render the checkbox per row inline). */
  selectable?: boolean
  renderSelection?: (row: T) => React.ReactNode
  renderSelectionHeader?: () => React.ReactNode
}

export default function Table<T extends { id?: string | number } = Record<string, unknown>>({
  columns,
  data,
  onRowClick,
  isLoading,
  emptyMessage = 'No records match',
  emptyAction,
  sortKey,
  sortDir,
  onSort,
  selectable,
  renderSelection,
  renderSelectionHeader,
}: TableProps<T>) {
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
    return (
      <div className="text-center py-12 text-base text-muted-foreground bg-card border border-border rounded-[14px]">
        <p>{emptyMessage}</p>
        {emptyAction && (
          <button
            type="button"
            onClick={emptyAction.onClick}
            className="mt-3 text-[13px] font-bold text-[#2A6BD4] dark:text-[#6FA0E8] hover:underline underline-offset-2 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#FFD60A] rounded-sm"
          >
            {emptyAction.label}
          </button>
        )}
      </div>
    )
  }

  return (
    <div className="overflow-x-auto border border-border rounded-[14px] bg-card elev-subtle">
      <table className="w-full text-base">
        <thead className="sticky top-0 z-10 bg-muted">
          <tr>
            {selectable && (
              <th className="w-10 px-3 py-3 text-left">
                {renderSelectionHeader?.()}
              </th>
            )}
            {columns.map(col => {
              const isSorted = sortKey === col.key && sortDir
              return (
                <th
                  key={col.key}
                  scope="col"
                  style={col.width ? { width: col.width } : undefined}
                  className={clsx(
                    'px-4 py-3 text-[12px] font-bold uppercase tracking-[0.06em] text-muted-foreground',
                    col.numeric ? 'text-right' : 'text-left',
                  )}
                >
                  {col.sortable && onSort ? (
                    <button
                      type="button"
                      onClick={() => onSort(col.key)}
                      className="inline-flex items-center gap-1 font-bold tracking-[0.06em] uppercase text-[12px] hover:text-foreground motion-fast transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#FFD60A] rounded-sm"
                      aria-sort={
                        isSorted ? (sortDir === 'asc' ? 'ascending' : 'descending') : 'none'
                      }
                    >
                      {col.label}
                      {isSorted && sortDir === 'asc' && (
                        <ChevronUp size={12} className="text-[#2A6BD4] dark:text-[#6FA0E8]" />
                      )}
                      {isSorted && sortDir === 'desc' && (
                        <ChevronDown size={12} className="text-[#2A6BD4] dark:text-[#6FA0E8]" />
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
          {data.map((row, i) => {
            const rowId = typeof row === 'object' && row && 'id' in row ? row.id : i
            return (
              <tr
                key={rowId as string | number}
                onClick={() => onRowClick?.(row)}
                className={clsx(
                  'border-t border-border motion-fast transition-colors',
                  // Alternating zebra — subtle warm wash on odd rows.
                  i % 2 === 1 && 'bg-muted/30',
                  onRowClick && 'cursor-pointer hover:bg-muted',
                )}
              >
                {selectable && (
                  <td className="w-10 px-3 py-3 align-middle">
                    {renderSelection?.(row)}
                  </td>
                )}
                {columns.map(col => {
                  const value = col.render
                    ? col.render(row)
                    : ((row as Record<string, unknown>)[col.key] as React.ReactNode)
                  return (
                    <td
                      key={col.key}
                      className={clsx(
                        'px-4 py-3 text-foreground align-middle',
                        col.numeric ? 'text-right tabular-nums' : 'text-left',
                      )}
                    >
                      {value}
                    </td>
                  )
                })}
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
