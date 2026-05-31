import { useState } from 'react'
import Button from '../../../../components/ui/Button'
import Input from '../../../../components/ui/Input'
import Select from '../../../../components/ui/Select'
import type { ConstraintCategory, ConstraintChip } from '../../../../types/search'
import {
  DEGREE_OPTIONS,
  FORMAT_OPTIONS,
  SEASON_OPTIONS,
  SELECTIVITY_OPTIONS,
} from './constants'
import {
  decodeRange,
  encodeRange,
  formatBudgetDisplay,
  formatDurationDisplay,
} from './chipUtils'

// Spec 10 §4 — the editor a chip opens (and the "+ Add" flow reuses). Each
// category gets the right control; Apply hands back a fully-formed chip.

interface ChipControlsProps {
  category: ConstraintCategory
  initial?: ConstraintChip
  onApply: (chip: ConstraintChip) => void
  onCancel?: () => void
}

const optionLabel = (opts: { value: string; label: string }[], value: string) =>
  opts.find(o => o.value === value)?.label ?? value

// Constraint values can arrive in variant forms (the parser emits "master",
// the agent may emit "masters") — resolve to the matching option so the editor
// shows the correct current selection. Singular/plural-insensitive.
const _norm = (s: string) => s.trim().toLowerCase().replace(/['’]/g, '').replace(/s$/, '')
function resolveOption(opts: { value: string; label: string }[], initial?: string): string {
  if (!initial) return opts[0].value
  const exact = opts.find(o => o.value === initial)
  if (exact) return exact.value
  const n = _norm(initial)
  const fuzzy = opts.find(o => _norm(o.value) === n)
  return fuzzy ? fuzzy.value : opts[0].value
}

export default function ChipControls({ category, initial, onApply, onCancel }: ChipControlsProps) {
  const apply = (value: string, display: string) =>
    onApply({ category, value, display, confidence: 100, user_confirmed: true })

  // Text categories (major / location / other).
  if (category === 'major' || category === 'location' || category === 'other') {
    return <TextEditor category={category} initial={initial} onApply={apply} onCancel={onCancel} />
  }

  // Single-select categories.
  if (category === 'degree_level' || category === 'format' || category === 'selectivity') {
    const opts =
      category === 'degree_level'
        ? DEGREE_OPTIONS
        : category === 'format'
          ? FORMAT_OPTIONS
          : SELECTIVITY_OPTIONS
    return <SelectEditor opts={opts} initial={initial?.value} onApply={apply} onCancel={onCancel} />
  }

  if (category === 'budget' || category === 'duration') {
    return <RangeEditor category={category} initial={initial} onApply={apply} onCancel={onCancel} />
  }

  // start_term
  return <StartTermEditor initial={initial} onApply={apply} onCancel={onCancel} />
}

function Footer({ onApply, onCancel, disabled }: { onApply: () => void; onCancel?: () => void; disabled?: boolean }) {
  return (
    <div className="flex justify-end gap-2 mt-3">
      {onCancel && (
        <Button variant="tertiary" size="sm" onClick={onCancel}>
          Cancel
        </Button>
      )}
      <Button variant="secondary" size="sm" onClick={onApply} disabled={disabled}>
        Apply
      </Button>
    </div>
  )
}

function TextEditor({
  category,
  initial,
  onApply,
  onCancel,
}: {
  category: ConstraintCategory
  initial?: ConstraintChip
  onApply: (value: string, display: string) => void
  onCancel?: () => void
}) {
  const [text, setText] = useState(initial?.display ?? '')
  const placeholder =
    category === 'major' ? 'e.g. computer science' : category === 'location' ? 'e.g. California' : 'e.g. research-heavy'
  const submit = () => {
    const t = text.trim()
    if (!t) return
    const value = category === 'location' ? t : t.toLowerCase()
    onApply(value, t)
  }
  return (
    <div className="w-60">
      <Input
        label={category === 'major' ? 'Field of study' : category === 'location' ? 'Location' : 'Note'}
        uiSize="sm"
        value={text}
        autoFocus
        placeholder={placeholder}
        onChange={e => setText(e.target.value)}
        onKeyDown={e => {
          if (e.key === 'Enter') submit()
        }}
      />
      <Footer onApply={submit} onCancel={onCancel} disabled={!text.trim()} />
    </div>
  )
}

function SelectEditor({
  opts,
  initial,
  onApply,
  onCancel,
}: {
  opts: { value: string; label: string }[]
  initial?: string
  onApply: (value: string, display: string) => void
  onCancel?: () => void
}) {
  const [value, setValue] = useState(resolveOption(opts, initial))
  return (
    <div className="w-56">
      <Select
        uiSize="sm"
        options={opts}
        value={value}
        onChange={e => setValue(e.target.value)}
      />
      <Footer onApply={() => onApply(value, optionLabel(opts, value))} onCancel={onCancel} />
    </div>
  )
}

function RangeEditor({
  category,
  initial,
  onApply,
  onCancel,
}: {
  category: 'budget' | 'duration'
  initial?: ConstraintChip
  onApply: (value: string, display: string) => void
  onCancel?: () => void
}) {
  const seed = initial ? decodeRange(initial.value) : {}
  const [min, setMin] = useState(seed.min != null ? String(seed.min) : '')
  const [max, setMax] = useState(seed.max != null ? String(seed.max) : '')
  const unit = category === 'budget' ? 'Annual tuition ($)' : 'Duration (months)'
  const submit = () => {
    const range = {
      min: min.trim() ? Number(min) : undefined,
      max: max.trim() ? Number(max) : undefined,
    }
    const value = encodeRange(range)
    if (!value) return
    const display = category === 'budget' ? formatBudgetDisplay(range) : formatDurationDisplay(range)
    onApply(value, display)
  }
  return (
    <div className="w-64">
      <p className="text-[13px] font-semibold text-muted-foreground mb-1.5">{unit}</p>
      <div className="flex items-center gap-2">
        <Input uiSize="sm" type="number" min={0} placeholder="Min" value={min} onChange={e => setMin(e.target.value)} />
        <span className="text-muted-foreground text-sm">–</span>
        <Input uiSize="sm" type="number" min={0} placeholder="Max" value={max} onChange={e => setMax(e.target.value)} />
      </div>
      <Footer onApply={submit} onCancel={onCancel} disabled={!min.trim() && !max.trim()} />
    </div>
  )
}

function StartTermEditor({
  initial,
  onApply,
  onCancel,
}: {
  initial?: ConstraintChip
  onApply: (value: string, display: string) => void
  onCancel?: () => void
}) {
  const [season, year] = (initial?.value ?? '').split(' ')
  const [s, setS] = useState(season || 'fall')
  const [y, setY] = useState(year || '')
  const submit = () => {
    if (!/^20\d{2}$/.test(y.trim())) return
    const value = `${s} ${y.trim()}`
    const label = SEASON_OPTIONS.find(o => o.value === s)?.label ?? s
    onApply(value, `${label} ${y.trim()}`)
  }
  return (
    <div className="w-60">
      <p className="text-[13px] font-semibold text-muted-foreground mb-1.5">Start term</p>
      <div className="flex items-center gap-2">
        <Select uiSize="sm" options={SEASON_OPTIONS} value={s} onChange={e => setS(e.target.value)} />
        <Input uiSize="sm" type="number" placeholder="Year" value={y} onChange={e => setY(e.target.value)} />
      </div>
      <Footer onApply={submit} onCancel={onCancel} disabled={!/^20\d{2}$/.test(y.trim())} />
    </div>
  )
}
