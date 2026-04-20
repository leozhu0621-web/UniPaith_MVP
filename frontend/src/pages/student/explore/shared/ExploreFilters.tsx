import { useEffect, useRef, useState } from 'react'
import { ChevronDown, X, Filter } from 'lucide-react'
import {
  classifyInstitution,
  satTier,
  tuitionTier,
  CLASSIFICATION_OPTIONS,
  DEGREE_LEVEL_OPTIONS,
  DELIVERY_FORMAT_OPTIONS,
  SAT_OPTIONS,
  TUITION_OPTIONS,
  type InstitutionClassification,
  type SatTier,
  type TuitionTier,
} from './classifyInstitution'

/**
 * ExploreFilters — horizontal filter bar above the universities grid.
 *
 * Multi-select dropdowns for list-valued filters (Location, Setting, Type,
 * Degree level, Delivery format, Subjects, Career outcomes, SAT tier,
 * Tuition tier). Toggle pills for booleans (App open, International,
 * Study abroad, Honors).
 *
 * Filter state is controlled from outside via URL search params — this
 * component is pure UI and emits change events, never owns state.
 */

export interface FilterState {
  country: string[]
  setting: string[] // 'urban' | 'suburban' | 'rural'
  type: InstitutionClassification[]
  degreeLevel: string[]
  deliveryFormat: string[]
  subjects: string[]
  industries: string[]
  satTier: SatTier[]
  tuitionTier: TuitionTier[]
  // Boolean toggles
  appOpen: boolean
  international: boolean
  studyAbroad: boolean
  honors: boolean
}

export const EMPTY_FILTERS: FilterState = {
  country: [],
  setting: [],
  type: [],
  degreeLevel: [],
  deliveryFormat: [],
  subjects: [],
  industries: [],
  satTier: [],
  tuitionTier: [],
  appOpen: false,
  international: false,
  studyAbroad: false,
  honors: false,
}

interface UniversityForFilters {
  country?: string | null
  campus_setting?: string | null
  type?: string | null
  description_text?: string | null
  subjects_offered?: string[] | null
  top_industries?: string[] | null
  degree_types_offered?: string[] | null
  delivery_formats_offered?: string[] | null
  sat_avg?: number | null
  tuition_annual?: number | null
  next_deadline?: string | null
  supports_international?: boolean | null
  has_study_abroad?: boolean | null
  has_honors?: boolean | null
}

interface Props {
  universities: UniversityForFilters[]
  filters: FilterState
  onChange: (next: FilterState) => void
}

/** Options derived from the actual university list so we never offer filters
 *  that would return zero rows. */
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

/** Apply the current FilterState to the university list. */
export function applyFilters(
  universities: UniversityForFilters[],
  filters: FilterState,
): UniversityForFilters[] {
  const now = new Date()
  now.setHours(0, 0, 0, 0)

  return universities.filter(u => {
    if (filters.country.length && !filters.country.includes(u.country || '')) return false
    if (filters.setting.length && !filters.setting.includes((u.campus_setting || '').toLowerCase())) return false

    if (filters.type.length) {
      const c = classifyInstitution({ description_text: u.description_text, type: u.type })
      if (!filters.type.includes(c.code)) return false
    }

    if (filters.degreeLevel.length) {
      const offered = new Set(u.degree_types_offered ?? [])
      if (!filters.degreeLevel.some(d => offered.has(d))) return false
    }

    if (filters.deliveryFormat.length) {
      const offered = new Set(u.delivery_formats_offered ?? [])
      if (!filters.deliveryFormat.some(d => offered.has(d))) return false
    }

    if (filters.subjects.length) {
      const offered = new Set(u.subjects_offered ?? [])
      if (!filters.subjects.some(s => offered.has(s))) return false
    }

    if (filters.industries.length) {
      const offered = new Set(u.top_industries ?? [])
      if (!filters.industries.some(i => offered.has(i))) return false
    }

    if (filters.satTier.length) {
      const t = satTier(u.sat_avg)
      if (!t || !filters.satTier.includes(t)) return false
    }

    if (filters.tuitionTier.length) {
      const t = tuitionTier(u.tuition_annual)
      if (!t || !filters.tuitionTier.includes(t)) return false
    }

    if (filters.appOpen) {
      if (!u.next_deadline) return false
      const dl = new Date(u.next_deadline)
      if (dl < now) return false
    }

    if (filters.international && !u.supports_international) return false
    if (filters.studyAbroad && !u.has_study_abroad) return false
    if (filters.honors && !u.has_honors) return false

    return true
  })
}

/** Count how many filters are active (each selection + each boolean). */
export function countActiveFilters(f: FilterState): number {
  return (
    f.country.length + f.setting.length + f.type.length +
    f.degreeLevel.length + f.deliveryFormat.length +
    f.subjects.length + f.industries.length +
    f.satTier.length + f.tuitionTier.length +
    (f.appOpen ? 1 : 0) + (f.international ? 1 : 0) +
    (f.studyAbroad ? 1 : 0) + (f.honors ? 1 : 0)
  )
}

export default function ExploreFilters({ universities, filters, onChange }: Props) {
  const { countries, subjects, industries } = deriveOptions(universities)
  const activeCount = countActiveFilters(filters)
  const clearAll = () => onChange(EMPTY_FILTERS)

  const toggleList = <K extends keyof FilterState>(key: K, value: string) => {
    const current = filters[key] as string[]
    const next = current.includes(value)
      ? current.filter(x => x !== value)
      : [...current, value]
    onChange({ ...filters, [key]: next } as FilterState)
  }

  const toggleBool = (key: 'appOpen' | 'international' | 'studyAbroad' | 'honors') => {
    onChange({ ...filters, [key]: !filters[key] })
  }

  return (
    <div className="mb-4">
      {/* Row 1: dropdown filters */}
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
          onToggle={v => toggleList('country', v)}
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
          onToggle={v => toggleList('setting', v)}
        />

        <FilterDropdown
          label="Type"
          active={filters.type.length}
          options={CLASSIFICATION_OPTIONS.map(c => ({ value: c.code, label: c.label }))}
          selected={filters.type}
          onToggle={v => toggleList('type', v)}
        />

        <FilterDropdown
          label="Degree"
          active={filters.degreeLevel.length}
          options={DEGREE_LEVEL_OPTIONS.map(d => ({ value: d.code, label: d.label }))}
          selected={filters.degreeLevel}
          onToggle={v => toggleList('degreeLevel', v)}
        />

        <FilterDropdown
          label="Format"
          active={filters.deliveryFormat.length}
          options={DELIVERY_FORMAT_OPTIONS.map(d => ({ value: d.code, label: d.label }))}
          selected={filters.deliveryFormat}
          onToggle={v => toggleList('deliveryFormat', v)}
        />

        {subjects.length > 0 && (
          <FilterDropdown
            label="Subjects"
            active={filters.subjects.length}
            options={subjects.map(s => ({ value: s, label: s }))}
            selected={filters.subjects}
            onToggle={v => toggleList('subjects', v)}
          />
        )}

        {industries.length > 0 && (
          <FilterDropdown
            label="Industries"
            active={filters.industries.length}
            options={industries.map(i => ({ value: i, label: i }))}
            selected={filters.industries}
            onToggle={v => toggleList('industries', v)}
          />
        )}

        <FilterDropdown
          label="SAT"
          active={filters.satTier.length}
          options={SAT_OPTIONS.map(s => ({ value: s.code, label: s.label }))}
          selected={filters.satTier}
          onToggle={v => toggleList('satTier', v)}
        />

        <FilterDropdown
          label="Tuition"
          active={filters.tuitionTier.length}
          options={TUITION_OPTIONS.map(t => ({ value: t.code, label: t.label }))}
          selected={filters.tuitionTier}
          onToggle={v => toggleList('tuitionTier', v)}
        />

        {activeCount > 0 && (
          <button
            onClick={clearAll}
            className="inline-flex items-center gap-1 text-[11px] text-student-text/70 hover:text-student-ink ml-auto"
          >
            <X size={12} /> Clear all
          </button>
        )}
      </div>

      {/* Row 2: boolean toggle pills */}
      <div className="flex flex-wrap items-center gap-2 mt-2">
        <TogglePill label="Open for applications" active={filters.appOpen} onClick={() => toggleBool('appOpen')} />
        <TogglePill label="International friendly" active={filters.international} onClick={() => toggleBool('international')} />
        <TogglePill label="Study abroad" active={filters.studyAbroad} onClick={() => toggleBool('studyAbroad')} />
        <TogglePill label="Honors available" active={filters.honors} onClick={() => toggleBool('honors')} />
      </div>

      {/* Active filter chip review */}
      {activeCount > 0 && (
        <div className="flex flex-wrap items-center gap-1.5 mt-2">
          {(['country', 'setting', 'type', 'degreeLevel', 'deliveryFormat',
             'subjects', 'industries', 'satTier', 'tuitionTier'] as const).flatMap(key =>
            (filters[key] as string[]).map(value => (
              <ActiveChip
                key={`${key}:${value}`}
                label={chipLabel(key, value)}
                onRemove={() => toggleList(key, value)}
              />
            )),
          )}
          {filters.appOpen && <ActiveChip label="Open for applications" onRemove={() => toggleBool('appOpen')} />}
          {filters.international && <ActiveChip label="International friendly" onRemove={() => toggleBool('international')} />}
          {filters.studyAbroad && <ActiveChip label="Study abroad" onRemove={() => toggleBool('studyAbroad')} />}
          {filters.honors && <ActiveChip label="Honors available" onRemove={() => toggleBool('honors')} />}
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
          <span className="inline-flex items-center justify-center min-w-[16px] h-[16px] px-1 rounded-full text-[9px] font-bold bg-white/20">
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

/* ── Toggle pill (boolean filter) ──────────────────────────────────── */

function TogglePill({ label, active, onClick }: { label: string; active: boolean; onClick: () => void }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`inline-flex items-center gap-1 px-2.5 py-1 text-[11px] font-medium rounded-full border transition-colors ${
        active
          ? 'bg-student text-white border-student'
          : 'bg-white text-student-ink border-divider hover:border-student hover:text-student'
      }`}
    >
      {label}
    </button>
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
  if (key === 'type') return CLASSIFICATION_OPTIONS.find(c => c.code === value)?.label ?? value
  if (key === 'degreeLevel') return DEGREE_LEVEL_OPTIONS.find(d => d.code === value)?.label ?? value
  if (key === 'deliveryFormat') return DELIVERY_FORMAT_OPTIONS.find(d => d.code === value)?.label ?? value
  if (key === 'satTier') return SAT_OPTIONS.find(s => s.code === value)?.label ?? value
  if (key === 'tuitionTier') return TUITION_OPTIONS.find(t => t.code === value)?.label ?? value
  return value
}
