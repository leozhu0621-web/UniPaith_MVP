/**
 * Spec 09 §5.1 + Spec 10 §4 — editable / removable constraint chips.
 *
 * The DiscoveryQueryInterpreter turns a natural-language query into structured
 * constraints; each renders as its own chip (`Category · Value ✕`). Click the
 * ✕ to remove it, or (for enum fields) click the label to edit in place — both
 * re-run the search live. Brand: pill, 1px `--accent` (cobalt) border, surface
 * bg, no gold in the chips region (Spec 10 §13).
 */
import { useState } from 'react'
import { Check, ChevronDown, X } from 'lucide-react'
import clsx from 'clsx'

export type ChipCategory =
  | 'degree_type'
  | 'country'
  | 'city'
  | 'max_tuition'
  | 'min_tuition'
  | 'delivery_format'

export interface SearchChip {
  id: string
  category: ChipCategory
  label: string
  value: string | number
  display: string
  editable?: boolean
}

const DEGREE_OPTIONS: Array<{ value: string; label: string }> = [
  { value: 'masters', label: "Master's" },
  { value: 'phd', label: 'PhD' },
  { value: 'bachelor', label: "Bachelor's" },
  { value: 'certificate', label: 'Certificate' },
]
const FORMAT_OPTIONS: Array<{ value: string; label: string }> = [
  { value: 'online', label: 'Online' },
  { value: 'hybrid', label: 'Hybrid' },
  { value: 'in_person', label: 'In person' },
]
const EDIT_OPTIONS: Partial<Record<ChipCategory, Array<{ value: string; label: string }>>> = {
  degree_type: DEGREE_OPTIONS,
  delivery_format: FORMAT_OPTIONS,
}

const DEGREE_LABELS: Record<string, string> = Object.fromEntries(
  DEGREE_OPTIONS.map(o => [o.value, o.label]),
)
const FORMAT_LABELS: Record<string, string> = Object.fromEntries(
  FORMAT_OPTIONS.map(o => [o.value, o.label]),
)

function moneyLabel(amount: number): string {
  return amount % 1000 === 0 ? `$${amount / 1000}k` : `$${amount.toLocaleString()}`
}

/** Display string for a chip value, used when an edit changes the value. */
export function displayForChip(category: ChipCategory, value: string | number): string {
  switch (category) {
    case 'degree_type':
      return DEGREE_LABELS[String(value)] ?? String(value)
    case 'delivery_format':
      return FORMAT_LABELS[String(value)] ?? String(value)
    case 'max_tuition':
      return `≤ ${moneyLabel(Number(value))}`
    case 'min_tuition':
      return `≥ ${moneyLabel(Number(value))}`
    default:
      return String(value)
  }
}

/** Build the chip list from the interpreter's `filters_applied` map. */
export function chipsFromFilters(filters: Record<string, unknown>): SearchChip[] {
  const chips: SearchChip[] = []
  const add = (
    category: ChipCategory,
    label: string,
    value: string | number,
    editable = false,
  ) => chips.push({ id: category, category, label, value, display: displayForChip(category, value), editable })

  if (typeof filters.degree_type === 'string') add('degree_type', 'Degree', filters.degree_type, true)
  if (typeof filters.delivery_format === 'string') add('delivery_format', 'Format', filters.delivery_format, true)
  if (typeof filters.country === 'string') add('country', 'Location', filters.country)
  if (typeof filters.city === 'string') add('city', 'City', filters.city)
  if (typeof filters.max_tuition === 'number') add('max_tuition', 'Budget', filters.max_tuition)
  if (typeof filters.min_tuition === 'number') add('min_tuition', 'Budget min', filters.min_tuition)
  return chips
}

interface ConstraintChipsProps {
  chips: SearchChip[]
  onRemove: (id: string) => void
  onEdit: (id: string, value: string) => void
}

export default function ConstraintChips({ chips, onRemove, onEdit }: ConstraintChipsProps) {
  const [openId, setOpenId] = useState<string | null>(null)
  if (chips.length === 0) return null

  return (
    <div className="flex flex-wrap items-center gap-2">
      {chips.map(chip => {
        const options = chip.editable ? EDIT_OPTIONS[chip.category] : undefined
        return (
          <div key={chip.id} className="relative">
            <span className="inline-flex items-center rounded-pill border border-cobalt bg-white text-xs text-student-ink">
              <button
                type="button"
                onClick={options ? () => setOpenId(prev => (prev === chip.id ? null : chip.id)) : undefined}
                disabled={!options}
                className={clsx(
                  'flex items-center gap-1 rounded-l-pill py-1 pl-2.5 pr-1.5',
                  options ? 'hover:bg-cobalt/5 cursor-pointer' : 'cursor-default',
                )}
                aria-haspopup={options ? 'listbox' : undefined}
                aria-expanded={options ? openId === chip.id : undefined}
              >
                <span className="text-slate">{chip.label}</span>
                <span className="text-cobalt/40">·</span>
                <span className="font-semibold">{chip.display}</span>
                {options && <ChevronDown size={11} className="ml-0.5 text-slate" />}
              </button>
              <button
                type="button"
                onClick={() => onRemove(chip.id)}
                aria-label={`Remove ${chip.label} filter`}
                className="rounded-r-pill py-1 pl-0.5 pr-2 text-slate transition-colors hover:text-error"
              >
                <X size={12} />
              </button>
            </span>

            {options && openId === chip.id && (
              <>
                <div className="fixed inset-0 z-10" onClick={() => setOpenId(null)} aria-hidden />
                <div
                  className="absolute left-0 z-20 mt-1 min-w-[150px] rounded-lg border border-stone bg-white py-1 elev-raised"
                  role="listbox"
                >
                  {options.map(option => (
                    <button
                      key={option.value}
                      type="button"
                      role="option"
                      aria-selected={String(chip.value) === option.value}
                      onClick={() => {
                        if (String(chip.value) !== option.value) onEdit(chip.id, option.value)
                        setOpenId(null)
                      }}
                      className="flex w-full items-center justify-between px-3 py-1.5 text-xs text-student-ink hover:bg-muted"
                    >
                      {option.label}
                      {String(chip.value) === option.value && <Check size={12} className="text-cobalt" />}
                    </button>
                  ))}
                </div>
              </>
            )}
          </div>
        )
      })}
    </div>
  )
}
