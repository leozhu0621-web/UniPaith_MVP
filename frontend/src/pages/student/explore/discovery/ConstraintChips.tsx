import { useState } from 'react'
import clsx from 'clsx'
import { HelpCircle, Plus, X } from 'lucide-react'
import Popover from '../../../../components/ui/Popover'
import type { ConstraintCategory, ConstraintChip } from '../../../../types/search'
import ChipControls from './ChipControls'
import { ADDABLE_CATEGORIES, CATEGORY_LABELS } from './constants'
import { categoryLabel, withChipId } from './chipUtils'

// Spec 10 §4 — the constraint-chip strip. Each chip: click label → edit
// popover, ✕ → remove. Low-confidence chips (<70, unconfirmed) show a `?` and
// a "did you mean" confirm. Trailing "+ Add" adds a chip by category.

interface ConstraintChipsProps {
  chips: ConstraintChip[]
  onApplyEdit: (id: string, chip: ConstraintChip) => void
  onRemove: (id: string) => void
  onAdd: (chip: ConstraintChip) => void
  onConfirm: (id: string) => void
}

export default function ConstraintChips({
  chips,
  onApplyEdit,
  onRemove,
  onAdd,
  onConfirm,
}: ConstraintChipsProps) {
  return (
    <div className="flex flex-wrap items-center gap-2" data-testid="chip-strip">
      {chips.map(chip => (
        <Chip
          key={chip.id}
          chip={chip}
          onApply={c => onApplyEdit(chip.id as string, c)}
          onRemove={() => onRemove(chip.id as string)}
          onConfirm={() => onConfirm(chip.id as string)}
        />
      ))}
      <AddChip onAdd={onAdd} />
    </div>
  )
}

function Chip({
  chip,
  onApply,
  onRemove,
  onConfirm,
}: {
  chip: ConstraintChip
  onApply: (chip: ConstraintChip) => void
  onRemove: () => void
  onConfirm: () => void
}) {
  const lowConf = chip.confidence < 70 && !chip.user_confirmed
  return (
    <span
      className={clsx(
        'inline-flex items-center rounded-pill border bg-card text-foreground text-[13px] h-8',
        lowConf ? 'border-warning' : 'border-secondary',
      )}
    >
      <Popover
        align="start"
        trigger={
          <span
            className={clsx(
              'inline-flex items-center gap-1 pl-3 pr-2 h-8 rounded-l-pill hover:bg-muted transition-colors',
            )}
          >
            <span className="text-muted-foreground">{categoryLabel(chip.category)}</span>
            <span className="text-muted-foreground" aria-hidden="true">·</span>
            <span className="font-semibold">{chip.display}</span>
            {lowConf && <HelpCircle size={13} className="text-warning ml-0.5" />}
          </span>
        }
      >
        {close => (
          <div>
            {lowConf && (
              <p className="text-xs text-muted-foreground mb-2">
                Just to confirm — did you mean <span className="font-semibold text-foreground">{chip.display}</span>?
              </p>
            )}
            <ChipControls
              category={chip.category}
              initial={chip}
              onApply={c => {
                onApply(c)
                close()
              }}
              onCancel={close}
            />
            {lowConf && (
              <button
                type="button"
                onClick={() => {
                  onConfirm()
                  close()
                }}
                className="mt-2 text-xs font-semibold text-secondary hover:underline"
              >
                Yes, that's right
              </button>
            )}
          </div>
        )}
      </Popover>
      <button
        type="button"
        onClick={onRemove}
        aria-label={`Remove ${categoryLabel(chip.category)} ${chip.display}`}
        className={clsx(
          'inline-flex items-center justify-center w-8 h-8 rounded-r-pill border-l text-muted-foreground',
          'hover:bg-muted hover:text-error transition-colors',
          lowConf ? 'border-warning/40' : 'border-secondary/40',
        )}
      >
        <X size={14} />
      </button>
    </span>
  )
}

function AddChip({ onAdd }: { onAdd: (chip: ConstraintChip) => void }) {
  const [cat, setCat] = useState<ConstraintCategory | null>(null)
  return (
    <Popover
      align="start"
      trigger={
        <span className="inline-flex items-center gap-1 h-8 px-3 rounded-pill border border-dashed border-border text-muted-foreground text-[13px] hover:bg-muted hover:text-foreground transition-colors">
          <Plus size={14} /> Add
        </span>
      }
    >
      {close =>
        cat ? (
          <ChipControls
            category={cat}
            onApply={c => {
              onAdd(withChipId(c))
              setCat(null)
              close()
            }}
            onCancel={() => setCat(null)}
          />
        ) : (
          <div className="flex flex-col w-44">
            <p className="text-[11px] uppercase tracking-wide text-muted-foreground font-semibold mb-1 px-1">
              Add a constraint
            </p>
            {ADDABLE_CATEGORIES.map(c => (
              <button
                key={c}
                type="button"
                onClick={() => setCat(c)}
                className="text-left text-sm px-2 py-1.5 rounded-md hover:bg-muted text-foreground"
              >
                {CATEGORY_LABELS[c]}
              </button>
            ))}
          </div>
        )
      }
    </Popover>
  )
}
