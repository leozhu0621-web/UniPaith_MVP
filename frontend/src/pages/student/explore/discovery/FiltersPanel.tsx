import { useState } from 'react'
import clsx from 'clsx'
import { SlidersHorizontal } from 'lucide-react'
import Popover from '../../../../components/ui/Popover'
import Button from '../../../../components/ui/Button'
import Input from '../../../../components/ui/Input'
import Select from '../../../../components/ui/Select'
import type { SearchFilters } from '../../../../types/search'
import {
  CAMPUS_SETTING_OPTIONS,
  DEGREE_OPTIONS,
  FORMAT_OPTIONS,
  SELECTIVITY_OPTIONS,
} from './constants'
import {
  SELECTIVITY_BANDS,
  countActiveFilters,
  normalizeFilters,
  selectivityFromRange,
} from './filterUtils'

// Spec 10 §5 — the [Filters ▾] panel. Coexists with chips (§4): both are sent
// on every search and merged server-side. The active-facet count shows as an
// accent badge on the trigger (§13).

interface FiltersPanelProps {
  filters: SearchFilters
  onApply: (filters: SearchFilters) => void
}

export default function FiltersPanel({ filters, onApply }: FiltersPanelProps) {
  const count = countActiveFilters(filters)
  return (
    <Popover
      align="start"
      trigger={
        <span
          className={clsx(
            'inline-flex items-center gap-1.5 h-9 px-3 rounded-lg border bg-card text-sm transition-colors hover:bg-muted',
            count > 0 ? 'border-secondary text-foreground' : 'border-border text-foreground',
          )}
          data-testid="filters-trigger"
        >
          <SlidersHorizontal size={14} className="text-muted-foreground" />
          Filters
          {count > 0 && (
            <span
              className="ml-0.5 inline-flex items-center justify-center min-w-[18px] h-[18px] px-1 rounded-full bg-secondary text-white text-[11px] font-semibold"
              aria-label={`${count} active filters`}
            >
              {count}
            </span>
          )}
        </span>
      }
    >
      {close => (
        <FiltersForm
          initial={filters}
          onApply={f => {
            onApply(f)
            close()
          }}
          onClear={() => {
            onApply({})
            close()
          }}
        />
      )}
    </Popover>
  )
}

interface Draft {
  degree_types: string[]
  delivery_formats: string[]
  campus_setting: string
  selectivity: string
  min_tuition: string
  max_tuition: string
  min_duration: string
  max_duration: string
  program_name: string
  min_salary: string
  min_employment: string
  max_payback: string
}

const str = (n: number | null | undefined): string => (n == null ? '' : String(n))

function seed(f: SearchFilters): Draft {
  return {
    degree_types: f.degree_types ?? [],
    delivery_formats: f.delivery_formats ?? [],
    campus_setting: f.campus_setting ?? '',
    selectivity: selectivityFromRange(f.min_acceptance_rate, f.max_acceptance_rate),
    min_tuition: str(f.min_tuition),
    max_tuition: str(f.max_tuition),
    min_duration: str(f.min_duration_months),
    max_duration: str(f.max_duration_months),
    program_name: f.program_name ?? '',
    min_salary: str(f.min_median_salary),
    min_employment: f.min_employment_rate == null ? '' : String(Math.round(f.min_employment_rate * 100)),
    max_payback: str(f.max_payback_months),
  }
}

function build(d: Draft): SearchFilters {
  const num = (s: string): number | undefined => {
    const t = s.trim()
    if (t === '') return undefined
    const n = Number(t)
    return Number.isFinite(n) ? n : undefined
  }
  const f: SearchFilters = {}
  if (d.degree_types.length) f.degree_types = d.degree_types
  if (d.delivery_formats.length) f.delivery_formats = d.delivery_formats
  if (d.campus_setting) f.campus_setting = d.campus_setting
  if (d.selectivity) {
    const band = SELECTIVITY_BANDS[d.selectivity]
    if (band?.min != null) f.min_acceptance_rate = band.min
    if (band?.max != null) f.max_acceptance_rate = band.max
  }
  const minT = num(d.min_tuition)
  if (minT != null) f.min_tuition = minT
  const maxT = num(d.max_tuition)
  if (maxT != null) f.max_tuition = maxT
  const minD = num(d.min_duration)
  if (minD != null) f.min_duration_months = minD
  const maxD = num(d.max_duration)
  if (maxD != null) f.max_duration_months = maxD
  if (d.program_name.trim()) f.program_name = d.program_name.trim()
  const sal = num(d.min_salary)
  if (sal != null) f.min_median_salary = sal
  const emp = num(d.min_employment)
  if (emp != null) f.min_employment_rate = Math.max(0, Math.min(100, emp)) / 100
  const pay = num(d.max_payback)
  if (pay != null) f.max_payback_months = pay
  return normalizeFilters(f)
}

function FiltersForm({
  initial,
  onApply,
  onClear,
}: {
  initial: SearchFilters
  onApply: (f: SearchFilters) => void
  onClear: () => void
}) {
  const [d, setD] = useState<Draft>(() => seed(initial))
  const set = <K extends keyof Draft>(key: K, value: Draft[K]) => setD(prev => ({ ...prev, [key]: value }))
  const toggle = (key: 'degree_types' | 'delivery_formats', value: string) =>
    setD(prev => ({
      ...prev,
      [key]: prev[key].includes(value) ? prev[key].filter(v => v !== value) : [...prev[key], value],
    }))

  return (
    <div className="w-[min(20rem,calc(100vw-3rem))]">
      <div className="flex items-center justify-between mb-2">
        <p className="text-sm font-semibold text-foreground">Filters</p>
        <button type="button" onClick={onClear} className="text-xs text-muted-foreground hover:text-foreground">
          Clear all
        </button>
      </div>

      <div className="max-h-[55vh] overflow-y-auto -mr-1 pr-1 space-y-3.5">
        <Section label="Degree level">
          <ToggleRow options={DEGREE_OPTIONS} selected={d.degree_types} onToggle={v => toggle('degree_types', v)} />
        </Section>

        <Section label="Delivery format">
          <ToggleRow options={FORMAT_OPTIONS} selected={d.delivery_formats} onToggle={v => toggle('delivery_formats', v)} />
        </Section>

        <Section label="Campus setting">
          <Select
            uiSize="sm"
            placeholder="Any"
            options={CAMPUS_SETTING_OPTIONS}
            value={d.campus_setting}
            onChange={e => set('campus_setting', e.target.value)}
          />
        </Section>

        <Section label="Selectivity">
          <Select
            uiSize="sm"
            placeholder="Any"
            options={SELECTIVITY_OPTIONS}
            value={d.selectivity}
            onChange={e => set('selectivity', e.target.value)}
          />
        </Section>

        <Section label="Tuition / year ($)">
          <RangeRow
            min={d.min_tuition}
            max={d.max_tuition}
            onMin={v => set('min_tuition', v)}
            onMax={v => set('max_tuition', v)}
          />
        </Section>

        <Section label="Duration (months)">
          <RangeRow
            min={d.min_duration}
            max={d.max_duration}
            onMin={v => set('min_duration', v)}
            onMax={v => set('max_duration', v)}
          />
        </Section>

        <Section label="Program or school name">
          <Input
            uiSize="sm"
            placeholder="e.g. Tisch"
            value={d.program_name}
            onChange={e => set('program_name', e.target.value)}
          />
        </Section>

        <div className="pt-1">
          <p className="text-[11px] uppercase tracking-wide text-muted-foreground font-semibold mb-2">
            Outcomes
          </p>
          <div className="space-y-3">
            <Section label="Min. median salary ($)">
              <Input uiSize="sm" type="number" min={0} placeholder="e.g. 80000" value={d.min_salary} onChange={e => set('min_salary', e.target.value)} />
            </Section>
            <Section label="Min. employment rate (%)">
              <Input uiSize="sm" type="number" min={0} max={100} placeholder="e.g. 85" value={d.min_employment} onChange={e => set('min_employment', e.target.value)} />
            </Section>
            <Section label="Max. payback (months)">
              <Input uiSize="sm" type="number" min={0} placeholder="e.g. 24" value={d.max_payback} onChange={e => set('max_payback', e.target.value)} />
            </Section>
          </div>
        </div>
      </div>

      <div className="flex justify-end gap-2 pt-3 mt-2 border-t border-border">
        <Button variant="secondary" size="sm" onClick={() => onApply(build(d))}>
          Apply filters
        </Button>
      </div>
    </div>
  )
}

function Section({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <p className="text-[13px] font-medium text-foreground mb-1.5">{label}</p>
      {children}
    </div>
  )
}

function ToggleRow({
  options,
  selected,
  onToggle,
}: {
  options: { value: string; label: string }[]
  selected: string[]
  onToggle: (value: string) => void
}) {
  return (
    <div className="flex flex-wrap gap-1.5">
      {options.map(o => {
        const active = selected.includes(o.value)
        return (
          <button
            key={o.value}
            type="button"
            onClick={() => onToggle(o.value)}
            aria-pressed={active}
            className={clsx(
              'px-2.5 py-1 rounded-pill border text-[13px] transition-colors',
              active
                ? 'border-secondary bg-secondary/10 text-foreground font-medium'
                : 'border-border text-muted-foreground hover:bg-muted',
            )}
          >
            {o.label}
          </button>
        )
      })}
    </div>
  )
}

function RangeRow({
  min,
  max,
  onMin,
  onMax,
}: {
  min: string
  max: string
  onMin: (v: string) => void
  onMax: (v: string) => void
}) {
  return (
    <div className="flex items-center gap-2">
      <Input uiSize="sm" type="number" min={0} placeholder="Min" value={min} onChange={e => onMin(e.target.value)} />
      <span className="text-muted-foreground text-sm">–</span>
      <Input uiSize="sm" type="number" min={0} placeholder="Max" value={max} onChange={e => onMax(e.target.value)} />
    </div>
  )
}
