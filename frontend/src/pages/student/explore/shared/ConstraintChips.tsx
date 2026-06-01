import { useState } from 'react'
import { X, Sparkles, Check } from 'lucide-react'

/**
 * Discovery constraint chips (gap audit G-S3).
 *
 * Renders each LLM/rule-extracted search constraint as its OWN editable chip
 * instead of one free-text summary. Select constraints edit via an inline
 * dropdown; text/number constraints click-to-edit; every chip has an X that
 * removes it. Any change calls onChange with the new constraint map, which the
 * parent turns into a structured `searchPrograms` call + URL state.
 */

export type Constraints = Record<string, string | number>

interface ChipDef {
  label: string
  type: 'text' | 'number' | 'select'
  options?: [string, string][]
  format?: (v: string | number) => string
  prefix?: string
}

// Only these keys render as editable chips; anything else (region, parsed_query)
// is display-only context handled by the parent's interpretation line.
export const CHIP_DEFS: Record<string, ChipDef> = {
  subjects: { label: 'Field', type: 'text' },
  degree_type: {
    label: 'Degree',
    type: 'select',
    options: [
      ['bachelors', "Bachelor's"],
      ['masters', "Master's"],
      ['phd', 'PhD'],
      ['certificate', 'Certificate'],
    ],
  },
  country: { label: 'Location', type: 'text' },
  max_tuition: {
    label: 'Max tuition',
    type: 'number',
    format: v => `$${Number(v).toLocaleString()}/yr`,
  },
  delivery_format: {
    label: 'Format',
    type: 'select',
    options: [
      ['online', 'Online'],
      ['hybrid', 'Hybrid'],
      ['on_campus', 'On Campus'],
    ],
  },
  sort_by: {
    label: 'Sort',
    type: 'select',
    options: [
      ['tuition_asc', 'Lowest tuition'],
      ['tuition_desc', 'Highest tuition'],
      ['salary_desc', 'Highest salary'],
      ['employment_desc', 'Best employment'],
      ['deadline', 'Deadline'],
    ],
  },
}

const CHIP_ORDER = ['subjects', 'degree_type', 'country', 'max_tuition', 'delivery_format', 'sort_by']

function displayValue(key: string, value: string | number): string {
  const def = CHIP_DEFS[key]
  if (!def) return String(value)
  if (def.type === 'select') {
    return def.options?.find(([code]) => code === String(value))?.[1] ?? String(value)
  }
  if (def.format) return def.format(value)
  return String(value)
}

interface Props {
  constraints: Constraints
  region?: string | null
  interpretation?: string
  onChange: (next: Constraints) => void
  onClear: () => void
}

export default function ConstraintChips({ constraints, region, interpretation, onChange, onClear }: Props) {
  const [editing, setEditing] = useState<string | null>(null)
  const [draft, setDraft] = useState('')

  const keys = CHIP_ORDER.filter(k => k in constraints && constraints[k] !== '' && constraints[k] != null)
  if (keys.length === 0) return null

  const commit = (key: string, raw: string) => {
    const def = CHIP_DEFS[key]
    const next = { ...constraints }
    const trimmed = raw.trim()
    if (!trimmed) {
      delete next[key]
    } else {
      next[key] = def?.type === 'number' ? Number(trimmed.replace(/[^\d.]/g, '')) : trimmed
    }
    setEditing(null)
    onChange(next)
  }

  const remove = (key: string) => {
    const next = { ...constraints }
    delete next[key]
    onChange(next)
  }

  return (
    <div className="mb-4 rounded-lg border border-gold/30 bg-gold-soft/40 px-3 py-2.5">
      <div className="flex items-center gap-2 mb-2">
        <Sparkles size={12} className="text-gold flex-shrink-0" />
        <span className="text-[11px] font-bold uppercase tracking-wider text-slate">
          Search constraints
        </span>
        {interpretation && (
          <span className="text-[11px] text-slate/80 truncate flex-1">· {interpretation}</span>
        )}
        <button
          onClick={onClear}
          className="text-[11px] text-cobalt hover:text-cobalt-hover font-medium flex-shrink-0"
        >
          Clear all
        </button>
      </div>

      <div className="flex flex-wrap items-center gap-1.5">
        {keys.map(key => {
          const def = CHIP_DEFS[key]
          const isEditing = editing === key
          const label = def?.label ?? key

          // Inline select editor — change re-runs search immediately.
          if (def?.type === 'select' && isEditing) {
            return (
              <span key={key} className="inline-flex items-center rounded-pill border border-cobalt/40 bg-white pl-2 pr-1 py-0.5">
                <span className="text-[10px] font-bold uppercase tracking-wider text-slate mr-1.5">{label}</span>
                <select
                  autoFocus
                  value={String(constraints[key])}
                  onChange={e => commit(key, e.target.value)}
                  onBlur={() => setEditing(null)}
                  className="text-xs bg-transparent text-ink focus:outline-none cursor-pointer"
                >
                  {def.options!.map(([code, lbl]) => (
                    <option key={code} value={code}>{lbl}</option>
                  ))}
                </select>
              </span>
            )
          }

          // Inline text / number editor.
          if ((def?.type === 'text' || def?.type === 'number') && isEditing) {
            return (
              <span key={key} className="inline-flex items-center rounded-pill border border-cobalt/40 bg-white pl-2 pr-1 py-0.5">
                <span className="text-[10px] font-bold uppercase tracking-wider text-slate mr-1.5">{label}</span>
                <input
                  autoFocus
                  type={def.type === 'number' ? 'number' : 'text'}
                  value={draft}
                  onChange={e => setDraft(e.target.value)}
                  onKeyDown={e => {
                    if (e.key === 'Enter') commit(key, draft)
                    if (e.key === 'Escape') setEditing(null)
                  }}
                  className="w-24 text-xs bg-transparent text-ink focus:outline-none"
                />
                <button onClick={() => commit(key, draft)} className="p-0.5 text-cobalt hover:text-cobalt-hover" aria-label="Apply">
                  <Check size={12} />
                </button>
              </span>
            )
          }

          // Resting chip — click value to edit, X to remove.
          return (
            <span key={key} className="inline-flex items-center rounded-pill border border-stone bg-white pl-2 pr-1 py-0.5 group/chip">
              <button
                onClick={() => {
                  setDraft(String(constraints[key]))
                  setEditing(key)
                }}
                className="text-xs text-ink hover:text-cobalt transition-colors"
                title={`Edit ${label.toLowerCase()}`}
              >
                <span className="text-[10px] font-bold uppercase tracking-wider text-slate mr-1.5">{label}</span>
                {displayValue(key, constraints[key])}
                {key === 'country' && region ? <span className="text-slate/70"> · {region}</span> : null}
              </button>
              <button
                onClick={() => remove(key)}
                className="ml-1 p-0.5 text-slate hover:text-error rounded-full transition-colors"
                aria-label={`Remove ${label.toLowerCase()} constraint`}
              >
                <X size={12} />
              </button>
            </span>
          )
        })}
      </div>
    </div>
  )
}
