/**
 * Spec 13 — one saved program row: match card + curation bar (priority, status,
 * notes, tags, compare, start application).
 */
import { useState } from 'react'
import { ChevronDown, FileText, MoreHorizontal, Pencil, Plus, Trash2 } from 'lucide-react'
import { confirmDialog } from '../../../stores/confirm-store'

import ProgramCard from '../explore/cards/ProgramCard'
import MatchCard from '../match/MatchCard'
import Badge from '../../../components/ui/Badge'
import Button from '../../../components/ui/Button'
import type { SavedPriority, SavedProgram, SavedStatus } from '../../../types'
import { matchDualOf, programSummaryOf } from './savedUtils'

export const PRIORITY_CONFIG: Record<SavedPriority, { label: string; color: string }> = {
  considering: { label: 'Considering', color: 'bg-muted text-foreground' },
  planning_to_apply: { label: 'Planning to apply', color: 'bg-secondary/10 text-secondary' },
  applied: { label: 'Applied', color: 'bg-success-soft text-success' },
  dropped: { label: 'Dropped', color: 'bg-error-soft text-error' },
}

export const PRIORITY_ORDER: SavedPriority[] = [
  'considering',
  'planning_to_apply',
  'applied',
  'dropped',
]

const STATUS_VARIANT: Record<
  SavedStatus,
  'neutral' | 'info' | 'success' | 'warning' | 'danger'
> = {
  considering: 'neutral',
  application_started: 'info',
  submitted: 'info',
  accepted: 'success',
  rejected: 'danger',
  waitlisted: 'warning',
  dropped: 'neutral',
}

const STATUS_LABELS: Record<SavedStatus, string> = {
  considering: 'Considering',
  application_started: 'Application started',
  submitted: 'Submitted',
  accepted: 'Accepted',
  rejected: 'Rejected',
  waitlisted: 'Waitlisted',
  dropped: 'Dropped',
}

export interface SavedProgramRowProps {
  item: SavedProgram
  comparing: boolean
  compareDisabled?: boolean
  onToggleCompare: () => void
  onPriorityChange: (priority: SavedPriority) => void
  onRemove: () => void
  onStartApplication: () => void
  onSaveNotes: (notes: string) => void
  onSaveTags: (tags: string[]) => void
  onView: () => void
  tagSuggestions: string[]
  priorityPending?: boolean
  startAppPending?: boolean
  removePending?: boolean
}

export default function SavedProgramRow({
  item: sp,
  comparing,
  compareDisabled,
  onToggleCompare,
  onPriorityChange,
  onRemove,
  onStartApplication,
  onSaveNotes,
  onSaveTags,
  onView,
  tagSuggestions,
  priorityPending,
  startAppPending,
  removePending,
}: SavedProgramRowProps) {
  const [menuOpen, setMenuOpen] = useState(false)
  const [editingNotes, setEditingNotes] = useState(false)
  const [noteDraft, setNoteDraft] = useState(sp.notes ?? '')
  const [tagInput, setTagInput] = useState('')

  const isDropped = sp.priority === 'dropped'
  const dual = matchDualOf(sp)
  const canStart =
    sp.status === 'considering' && sp.priority !== 'dropped' && sp.priority !== 'applied'

  const saveNotes = () => {
    onSaveNotes(noteDraft.trim())
    setEditingNotes(false)
  }

  const addTag = () => {
    const t = tagInput.trim()
    if (!t || sp.tags.includes(t)) return
    onSaveTags([...sp.tags, t])
    setTagInput('')
  }

  return (
    <article
      className={`rounded-xl border border-border bg-card overflow-hidden ${isDropped ? 'opacity-75' : ''}`}
    >
      {/* Curation bar — Spec 13 wireframe: priority + notes above card actions */}
      <div className="flex flex-wrap items-center gap-2 px-3 py-2 border-b border-border bg-muted/30">
        <label className="inline-flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            checked={comparing}
            disabled={compareDisabled}
            onChange={onToggleCompare}
            className="rounded border-border"
            aria-label={`Compare ${sp.program_name ?? 'program'}`}
          />
          <span className="text-[10px] text-muted-foreground uppercase tracking-wide">Compare</span>
        </label>

        <div className="relative inline-block">
          <select
            value={sp.priority}
            onChange={e => onPriorityChange(e.target.value as SavedPriority)}
            disabled={priorityPending}
            aria-label={`Priority for ${sp.program_name ?? 'program'}`}
            className={`appearance-none text-xs font-medium rounded-full pl-2.5 pr-6 py-0.5 border-0 cursor-pointer ${PRIORITY_CONFIG[sp.priority].color}`}
          >
            {PRIORITY_ORDER.map(p => (
              <option key={p} value={p}>
                {PRIORITY_CONFIG[p].label}
              </option>
            ))}
          </select>
          <ChevronDown
            size={10}
            className="absolute right-1.5 top-1/2 -translate-y-1/2 pointer-events-none text-muted-foreground/60"
          />
        </div>

        <Badge variant={STATUS_VARIANT[sp.status] ?? 'neutral'} size="sm">
          {STATUS_LABELS[sp.status] ?? sp.status}
        </Badge>

        {sp.tags.map(tag => (
          <button
            key={tag}
            type="button"
            onClick={() => onSaveTags(sp.tags.filter(t => t !== tag))}
            className="inline-flex items-center gap-1 max-w-[140px] text-[10px] px-2 py-0.5 rounded-full bg-muted text-muted-foreground border border-border/50 hover:border-error/40"
            title={`${tag} — remove tag`}
          >
            <span className="truncate">{tag}</span>
            <span aria-hidden className="shrink-0">×</span>
          </button>
        ))}

        <span className="inline-flex items-center gap-1 min-w-[120px] flex-1 max-w-xs">
          <input
            list={`tags-${sp.program_id}`}
            value={tagInput}
            onChange={e => setTagInput(e.target.value)}
            onKeyDown={e => {
              if (e.key === 'Enter') {
                e.preventDefault()
                addTag()
              }
            }}
            placeholder="Add tag…"
            className="flex-1 text-[11px] border border-border rounded-md px-2 py-0.5 bg-card"
          />
          <button
            type="button"
            onClick={addTag}
            className="p-0.5 text-secondary"
            aria-label="Add tag"
          >
            <Plus size={12} />
          </button>
          <datalist id={`tags-${sp.program_id}`}>
            {tagSuggestions.map(t => (
              <option key={t} value={t} />
            ))}
          </datalist>
        </span>

        <div className="ml-auto flex items-center gap-1 relative">
          {canStart && (
            <Button
              size="sm"
              variant="secondary"
              onClick={onStartApplication}
              loading={startAppPending}
              className="text-xs whitespace-nowrap"
            >
              <FileText size={12} className="mr-1" />
              Start application →
            </Button>
          )}
          <button
            type="button"
            onClick={() => setMenuOpen(v => !v)}
            className="p-1.5 rounded-md text-muted-foreground hover:bg-muted"
            aria-label="More actions"
          >
            <MoreHorizontal size={16} />
          </button>
          {menuOpen && (
            <>
              <div className="fixed inset-0 z-10" onClick={() => setMenuOpen(false)} />
              <div className="absolute right-0 top-full mt-1 z-20 min-w-[140px] rounded-lg border border-border bg-card elev-raised py-1 text-sm shadow-lg">
                <button
                  type="button"
                  className="w-full text-left px-3 py-1.5 hover:bg-muted flex items-center gap-2"
                  onClick={() => {
                    setMenuOpen(false)
                    setNoteDraft(sp.notes ?? '')
                    setEditingNotes(true)
                  }}
                >
                  <Pencil size={12} />
                  {sp.notes ? 'Edit notes' : 'Add notes'}
                </button>
                <button
                  type="button"
                  className="w-full text-left px-3 py-1.5 hover:bg-muted text-error flex items-center gap-2"
                  onClick={async () => {
                    setMenuOpen(false)
                    const ok = await confirmDialog({
                      title: 'Remove from your shortlist?',
                      confirmLabel: 'Remove',
                      destructive: true,
                    })
                    if (ok) onRemove()
                  }}
                  disabled={removePending}
                >
                  <Trash2 size={12} />
                  Remove from list
                </button>
              </div>
            </>
          )}
        </div>
      </div>

      {(sp.notes || editingNotes) && (
        <div className="px-3 py-2 border-b border-border bg-card">
          {editingNotes ? (
            <div className="space-y-2">
              <textarea
                value={noteDraft}
                onChange={e => setNoteDraft(e.target.value)}
                className="w-full text-sm border border-border rounded-lg px-3 py-2 min-h-[72px] focus:outline-none focus:ring-2 focus:ring-ring"
                placeholder="Why I saved this, things to verify…"
              />
              <div className="flex gap-2 justify-end">
                <Button size="sm" variant="ghost" onClick={() => setEditingNotes(false)}>
                  Cancel
                </Button>
                <Button size="sm" variant="secondary" onClick={saveNotes}>
                  Save notes
                </Button>
              </div>
            </div>
          ) : (
            <p className="text-xs text-muted-foreground italic line-clamp-2">&ldquo;{sp.notes}&rdquo;</p>
          )}
        </div>
      )}

      {dual ? (
        <MatchCard
          match={dual}
          saved
          comparing={comparing}
          onSave={onRemove}
          onCompare={onToggleCompare}
          onView={onView}
        />
      ) : (
        <ProgramCard
          program={programSummaryOf(sp)}
          saved
          comparing={comparing}
          onSave={onRemove}
          onCompare={onToggleCompare}
          onView={onView}
        />
      )}
    </article>
  )
}
