import clsx from 'clsx'
import { ChevronDown } from 'lucide-react'
import Popover from '../../../../components/ui/Popover'
import type { SortOption } from '../../../../types/search'
import { SORT_OPTIONS } from './constants'

// Spec 10 §6 — sort menu.
interface SortMenuProps {
  value: SortOption
  onChange: (value: SortOption) => void
}

export default function SortMenu({ value, onChange }: SortMenuProps) {
  const label = SORT_OPTIONS.find(o => o.value === value)?.label ?? 'Relevance'
  return (
    <Popover
      align="end"
      trigger={
        <span className="inline-flex items-center gap-1.5 h-9 px-3 rounded-lg border border-border bg-card text-sm text-foreground hover:bg-muted transition-colors">
          Sort: <span className="font-semibold">{label}</span>
          <ChevronDown size={14} className="text-muted-foreground" />
        </span>
      }
    >
      {close => (
        <div className="flex flex-col w-56">
          {SORT_OPTIONS.map(o => (
            <button
              key={o.value}
              type="button"
              onClick={() => {
                onChange(o.value)
                close()
              }}
              className={clsx(
                'text-left text-sm px-2 py-1.5 rounded-md hover:bg-muted',
                o.value === value ? 'text-secondary font-semibold' : 'text-foreground',
              )}
            >
              {o.label}
            </button>
          ))}
        </div>
      )}
    </Popover>
  )
}
