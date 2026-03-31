import clsx from 'clsx'
import Skeleton from './Skeleton'

export interface Column<T extends object = Record<string, unknown>> {
  key: string
  label: string
  render?: (row: T) => React.ReactNode
}

interface TableProps<T extends object> {
  columns: Column<T>[]
  data: T[]
  onRowClick?: (row: T) => void
  isLoading?: boolean
  emptyMessage?: string
}

export default function Table<T extends object>({
  columns,
  data,
  onRowClick,
  isLoading,
  emptyMessage = 'No data',
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
      <div className="text-center py-12 text-sm text-gray-500">{emptyMessage}</div>
    )
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-gray-200">
            {columns.map(col => (
              <th key={col.key} className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                {col.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.map((row, i) => (
            <tr
              key={String((row as Record<string, unknown>).id ?? i)}
              onClick={() => onRowClick?.(row)}
              className={clsx(
                'border-b border-gray-100',
                i % 2 === 1 && 'bg-gray-50/50',
                onRowClick && 'cursor-pointer hover:bg-gray-100'
              )}
            >
              {columns.map(col => (
                <td key={col.key} className="px-4 py-3 text-gray-700">
                  {col.render
                    ? col.render(row)
                    : String((row as Record<string, unknown>)[col.key] ?? '')}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
