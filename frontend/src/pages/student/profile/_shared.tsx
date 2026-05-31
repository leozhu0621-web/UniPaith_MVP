/**
 * Shared building blocks for the Universal Profile tabs (spec 10).
 * Brand-token classes only: charcoal/slate text, cobalt accent, gold punctuation,
 * divider borders. No decorative imagery.
 */
import type { ReactNode } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Pencil, Plus, Trash2 } from 'lucide-react'
import type { LucideIcon } from 'lucide-react'

import { getProfile } from '../../../api/students'
import Button from '../../../components/ui/Button'
import Card from '../../../components/ui/Card'
import type { StudentProfile } from '../../../types'

export function useProfile() {
  return useQuery<StudentProfile>({ queryKey: ['profile'], queryFn: getProfile })
}

/** Compact relative time — "just now" / "2h ago" / "3d ago" (spec §24 copy). */
export function relativeTime(iso?: string | null): string {
  if (!iso) return 'not yet'
  const diff = Date.now() - new Date(iso).getTime()
  const m = Math.round(diff / 60000)
  if (m < 1) return 'just now'
  if (m < 60) return `${m}m ago`
  const h = Math.round(m / 60)
  if (h < 24) return `${h}h ago`
  const d = Math.round(h / 24)
  if (d < 30) return `${d}d ago`
  const mo = Math.round(d / 30)
  if (mo < 12) return `${mo}mo ago`
  return `${Math.round(mo / 12)}y ago`
}

/** A profile section: header (icon + title + count + last-updated) with add/edit affordances. */
export function SectionCard({
  title,
  icon: Icon,
  count,
  onAdd,
  onEdit,
  lastUpdated,
  children,
}: {
  title: string
  icon?: LucideIcon
  count?: number
  onAdd?: () => void
  onEdit?: () => void
  lastUpdated?: string | null
  children: ReactNode
}) {
  return (
    <Card className="p-5">
      <div className="flex items-start justify-between gap-3 mb-3">
        <div className="flex items-center gap-2 min-w-0">
          {Icon && <Icon size={16} className="text-cobalt shrink-0" />}
          <h3 className="font-semibold text-charcoal truncate">{title}</h3>
          {typeof count === 'number' && count > 0 && <span className="text-xs text-slate">{count}</span>}
        </div>
        <div className="flex items-center gap-2 shrink-0">
          {lastUpdated && <span className="text-xs text-slate hidden sm:inline">Updated {relativeTime(lastUpdated)}</span>}
          {onEdit && (
            <Button size="sm" variant="ghost" onClick={onEdit} aria-label={`Edit ${title}`}>
              <Pencil size={14} />
            </Button>
          )}
          {onAdd && (
            <Button size="sm" variant="ghost" onClick={onAdd} aria-label={`Add to ${title}`}>
              <Plus size={14} />
            </Button>
          )}
        </div>
      </div>
      {children}
    </Card>
  )
}

/** A list row with edit/delete actions on the right. */
export function ItemRow({
  children,
  onEdit,
  onDelete,
}: {
  children: ReactNode
  onEdit?: () => void
  onDelete?: () => void
}) {
  return (
    <div className="flex justify-between items-start gap-3 border-b border-divider pb-3 last:border-0 last:pb-0">
      <div className="min-w-0">{children}</div>
      {(onEdit || onDelete) && (
        <div className="flex gap-1 shrink-0">
          {onEdit && (
            <Button size="sm" variant="ghost" onClick={onEdit} aria-label="Edit">
              <Pencil size={12} />
            </Button>
          )}
          {onDelete && (
            <Button size="sm" variant="ghost" onClick={onDelete} aria-label="Delete">
              <Trash2 size={12} />
            </Button>
          )}
        </div>
      )}
    </div>
  )
}

/** Branded empty-state line — explains what would put data here (design-system §12). */
export function EmptyHint({ children }: { children: ReactNode }) {
  return <p className="text-sm text-slate">{children}</p>
}

/** 5-dot completeness meter (gold filled, border empty) — Overview cluster cards. */
export function DotMeter({ pct }: { pct: number }) {
  const filled = Math.round(Math.min(100, Math.max(0, pct)) / 20)
  return (
    <div className="flex items-center gap-1" aria-hidden>
      {[0, 1, 2, 3, 4].map(i => (
        <span
          key={i}
          className={`w-1.5 h-1.5 rounded-full ${i < filled ? 'bg-gold' : 'bg-stone'}`}
        />
      ))}
    </div>
  )
}
