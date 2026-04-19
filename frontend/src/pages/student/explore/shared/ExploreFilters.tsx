import { useEffect, useRef, useState } from 'react'
import { ChevronDown, X, Filter } from 'lucide-react'
import {
  classifyInstitution,
  sizeBucket,
  CLASSIFICATION_OPTIONS,
  SIZE_OPTIONS,
  type InstitutionClassification,
  type SizeBucket,
} from './classifyInstitution'

/**
 * ExploreFilters — horizontal filter bar above the universities grid.
 *
 * Six multi-select filters: Location · Setting · Size · Type · Subjects
 * · Career outcomes. Each renders as a dropdown chip; active selections
 * show a count badge. Clearing and resetting are both supported.
 *
 * Filter state is controlled from outside via URL search params — this
 * component is pure UI and emits change events, never owns state.
 */

export interface FilterState {
  country: string[]
  setting: string[] // 'urban' | 'suburban' | 'rural'
  size: SizeBucket[]
  type: InstitutionClassification[]
  subjects: string[]
  industries: string[]
}

export const EMPTY_FILTERS: FilterState = {
  country: [],
  setting: [],
  size: [],
  type: [],
  subjects: [],
  industries: [],
}

interface UniversityForFilters {
  country?: string | null
  campus_setting?: string | null
  student_body_size?: number | null
  type?: string | null
  description_text?: string | null
  subjects_offered?: string[] | null
  top_industries?: string[] | null
}

interface Props {
  universities: UniversityForFilters[]
  filters: FilterState
  onChange: (next: FilterState) => void
}

/** Keep the filter-pill options derived from the actual university list so
 *  we don't offer filters that would return zero rows. */
function deriveOptions(universities: UniversityForFilters[]) {
  const countries = new Set<string>()
  const subjects = new Set<string>()
  const industries = new Set<string>()

  for (const u of universities) {
    if (u.country) countries.add(u.country)
    if (Array.isArray(u.subjects_offered)) u.subjects_offered.forEach(s => s && subjects.add(s))
    if (Array.isArray(u.top_industries)) u.top_industries.forEach(i => i && industries.add(i))
  }

  return {
    countries: Array.from(countries).sort(),
    subjects: Array.from(subjects).sort(),
    industries: Array.from(industries).sort(),
  }
}

/** Filter a list of universities by the current FilterState. */
export function applyFilters(
  universities: UniversityForFilters[],
  filters: FilterState,
): UniversityForFilters[] {
  return universities.filter(u => {
    if (filters.country.length && !filters.country.includes(u.country || '')) return false
    if (filters.setting.length && !filters.setting.includes((u.campus_setting || '').toLowerCase())) return false

    if (filters.size.length) {
      const s = sizeBucket(u.student_body_size)
      if (!s || !filters.size.includes(s)) return false
    }

    if (filters.type.length) {
      const c = classifyInstitution({ description_text: u.description_text, type: u.type })
      if (!filters.type.includes(c.code)) return false
    }

    if (filters.subjects.length) {
      const offered = new Set(u.subjects_offered ?? [])
      if (!filters.subjects.some(s => offered.has(s))) return false
    }

    if (filters.industries.length) {
      const offered = new Set(u.top_industries ?? [])
      if (!filters.industries.some(i => offered.has(i))) return false
    }

    return true
  })
}

export default function ExploreFilters({ universities, filters, onChange }: Props) {
  const { countries, subjects, industries } = deriveOptions(universities)

  const activeCount =
    filters.country.length + filters.setting.length + filters.size.length +
    filters.type.length + filters.subjects.length + filters.industries.length

  const clearAll = () => onChange(EMPTY_FILTERS)

  const toggle = <K extends keyof FilterState>(key: K, value: FilterState[K][number]) => {
    const current = filters[key] as string[]
    const next = current.includes(value as string)
      ? current.filter(x => x !== value)
      : [...current, value as string]
    onChange({ ...filters, [key]: next } as FilterState)
  }

  return (
    <div className="mb-4">
      <div className="flex items-center gap-2 flex-wrap">
        <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-student-text/70 uppercase tracking-wider mr-1">
          <Filter size={11} />
          Filter
        </span>

        <FilterDropdown
          label="Location"
          active={filters.country.length}
          options={countries.map(c => ({ value: c, label: c }))}
          selected={filters.country}
          onToggle={v => toggle('country', v)}
        />

        <FilterDropdown
          label="Setting"
          active={filters.setting.length}
          options={[
            { value: 'urban', label: 'Urban' },
            { value: 'suburban', label: 'Suburban' },
            { value: 'rural', label: 'Rural' },
          ]}
          selected={filters.setting}
          onToggle={v => toggle('setting', v)}
        />

        <FilterDropdown
          label="Size"
          active={filters.size.length}
          options={SIZE_OPTIONS.map(s => ({ value: s.code, label: `${s.label} (${s.hint})` }))}
          selected={filters.size}
          onToggle={v => toggle('size', v as SizeBucket)}
        />

        <FilterDropdown
          label="Type"
          active={filters.type.length}
          options={CLASSIFICATION_OPTIONS.map(c => ({ value: c.code, label: c.label }))}
          selected={filters.type}
          onToggle={v => toggle('type', v as InstitutionClassification)}
        />

        {subjects.length > 0 && (
          <FilterDropdown
            label="Subjects"
            active={filters.subjects.length}
            options={subjects.map(s => ({ value: s, label: s }))}
            selected={filters.subjects}
            onToggle={v => toggle('subjects', v)}
          />
        )}

        {industries.length > 0 && (
          <FilterDropdown
            label="Career outcomes"
            active={filters.industries.length}
            options={industries.map(i => ({ value: i, label: i }))}
            selected={filters.industries}
            onToggle={v => toggle('industries', v)}
          />
        )}

        {activeCount > 0 && (
          <button
            onClick={clearAll}
            className="inline-flex items-center gap-1 text-[11px] text-student-text/70 hover:text-student-ink ml-auto"
          >
            <X size={12} /> Clear all
          </button>
        )}
      </div>

      {/* Active filter chips */}
      {activeCount > 0 && (
        <div className="flex flex-wrap items-center gap-1.5 mt-2">
          {(['country', 'setting', 'size', 'type', 'subjects', 'industries'] as const).flatMap(key =>
            (filters[key] as string[]).map(value => (
              <ActiveChip
                key={`${key}:${value}`}
                label={chipLabel(key, value)}
                onRemove={() => toggle(key, value as any)}
              />
            )),
          )}
        </div>
      )}
    </div>
  )
}

/* ── Dropdown building block ───────────────────────────────────────── */

interface DropdownProps {
  label: string
  active: number
  options: Array<{ value: string; label: string }>
  selected: string[]
  onToggle: (value: string) => void
}

function FilterDropdown({ label, active, options, selected, onToggle }: DropdownProps) {
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)

  // Close on click outside
  useEffect(() => {
    if (!open) return
    const onClick = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener('mousedown', onClick)
    return () => document.removeEventListener('mousedown', onClick)
  }, [open])

  const hasActive = active > 0

  return (
    <div className="relative" ref={ref}>
      <button
        type="button"
        onClick={() => setOpen(o => !o)}
        className={`inline-flex items-center gap-1 px-2.5 py-1 text-[11px] font-medium rounded-full border transition-colors ${
          hasActive
            ? 'bg-student text-white border-student'
            : 'bg-white text-student-ink border-divider hover:border-student hover:text-student'
        }`}
      >
        {label}
        {hasActive && (
          <span className={`inline-flex items-center justify-center min-w-[16px] h-[16px] px-1 rounded-full text-[9px] font-bold ${
            hasActive ? 'bg-white/20' : 'bg-student-mist text-student'
          }`}>
            {active}
          </span>
        )}
        <ChevronDown size={10} className={open ? 'rotate-180 transition-transform' : 'transition-transform'} />
      </button>

      {open && (
        <div className="absolute z-40 top-full left-0 mt-1 min-w-[200px] max-h-80 overflow-y-auto rounded-lg border border-divider bg-white shadow-lg">
          {options.length === 0 ? (
            <p className="text-[11px] text-student-text/60 italic px-3 py-2">No options available</p>
          ) : (
            <ul className="py-1">
              {options.map(opt => {
                const isSelected = selected.includes(opt.value)
                return (
                  <li key={opt.value}>
                    <button
                      type="button"
                      onClick={() => onToggle(opt.value)}
                      className={`w-full flex items-center gap-2 px-3 py-1.5 text-[12px] text-left transition-colors ${
                        isSelected
                          ? 'bg-student-mist text-student'
                          : 'hover:bg-slate-50 text-student-ink'
                      }`}
                    >
                      <span className={`w-3.5 h-3.5 rounded border flex-shrink-0 flex items-center justify-center ${
                        isSelected ? 'bg-student border-student' : 'bg-white border-slate-300'
                      }`}>
                        {isSelected && (
                          <svg width="9" height="9" viewBox="0 0 20 20" fill="white">
                            <path fillRule="evenodd" clipRule="evenodd" d="M16.7 5.3a1 1 0 010 1.4l-8 8a1 1 0 01-1.4 0l-4-4a1 1 0 011.4-1.4L8 12.6l7.3-7.3a1 1 0 011.4 0z" />
                          </svg>
                        )}
                      </span>
                      {opt.label}
                    </button>
                  </li>
                )
              })}
            </ul>
          )}
        </div>
      )}
    </div>
  )
}

/* ── Active chip ────────────────────────────────────────────────────── */

function ActiveChip({ label, onRemove }: { label: string; onRemove: () => void }) {
  return (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 text-[10.5px] rounded-full bg-student-mist text-student border border-student/15">
      {label}
      <button
        type="button"
        onClick={onRemove}
        className="ml-0.5 text-student/70 hover:text-student"
        aria-label={`Remove ${label} filter`}
      >
        <X size={10} />
      </button>
    </span>
  )
}

/** Pretty label for a filter chip given the key + raw value. */
function chipLabel(key: keyof FilterState, value: string): string {
  if (key === 'setting') return value.charAt(0).toUpperCase() + value.slice(1)
  if (key === 'size') return SIZE_OPTIONS.find(s => s.code === value)?.label ?? value
  if (key === 'type') return CLASSIFICATION_OPTIONS.find(c => c.code === value)?.label ?? value
  return value
}
