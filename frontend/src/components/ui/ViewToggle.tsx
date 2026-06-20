import { LayoutGrid, List } from 'lucide-react'
import clsx from 'clsx'
import type { BrowseView } from '../../hooks/useBrowseView'

interface Props {
  value: BrowseView
  onChange: (v: BrowseView) => void
  className?: string
}

// Segmented grid / list control shared by every browse surface.
export default function ViewToggle({ value, onChange, className }: Props) {
  const opts: { v: BrowseView; Icon: typeof LayoutGrid; label: string }[] = [
    { v: 'grid', Icon: LayoutGrid, label: 'Grid view' },
    { v: 'list', Icon: List, label: 'List view' },
  ]
  return (
    <div role="group" aria-label="View" className={clsx('inline-flex items-center rounded-md border border-border overflow-hidden flex-shrink-0', className)}>
      {opts.map(({ v, Icon, label }) => (
        <button
          key={v}
          type="button"
          onClick={() => onChange(v)}
          aria-pressed={value === v}
          aria-label={label}
          className={clsx(
            'inline-flex h-7 w-8 items-center justify-center transition-colors',
            value === v ? 'bg-secondary text-secondary-foreground' : 'text-muted-foreground hover:bg-muted',
          )}
        >
          <Icon size={14} />
        </button>
      ))}
    </div>
  )
}
