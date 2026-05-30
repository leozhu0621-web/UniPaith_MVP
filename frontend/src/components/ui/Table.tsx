import clsx from 'clsx'
import Skeleton from './Skeleton'

// Table — Spec/02-design-system.md §8. Muted sticky header with eyebrow labels;
// alternating rows; muted hover; 12y/16x cell padding.
interface Column {
  key: string
  label: string
  render?: (row: any) => React.ReactNode
  align?: 'left' | 'right'
  numeric?: boolean
}

interface TableProps {
  columns: Column[]
  data: any[]
  onRowClick?: (row: any) => void
  isLoading?: boolean
  emptyMessage?: string
}

export default function Table({ columns, data, onRowClick, isLoading, emptyMessage = 'No records match' }: TableProps) {
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

  return (
    <div className="overflow-x-auto rounded-lg border border-border">
      <table className="w-full text-sm">
        <thead className="sticky top-0 z-10">
          <tr className="bg-muted">
            {columns.map(col => (
              <th
                key={col.key}
                className={clsx(
                  'px-4 py-3 text-[11px] font-semibold uppercase tracking-wider text-muted-foreground',
                  col.align === 'right' || col.numeric ? 'text-right' : 'text-left'
                )}
              >
                {col.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.map((row, i) => (
            <tr
              key={row.id || i}
              onClick={() => onRowClick?.(row)}
              className={clsx(
                'border-t border-border',
                i % 2 === 1 && 'bg-muted/30',
                onRowClick && 'cursor-pointer hover:bg-muted transition-colors'
              )}
            >
              {columns.map(col => (
                <td
                  key={col.key}
                  className={clsx(
                    'px-4 py-3 text-foreground',
                    (col.align === 'right' || col.numeric) && 'text-right tabular-nums'
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
