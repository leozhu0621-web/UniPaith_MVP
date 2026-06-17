/**
 * Profile → Preferences tab (Spec/08 §12).
 * Structured pickers + importance weight sliders. Explicit Save (§10) +
 * debounced autosave (§19, Ship D input preservation) — the upsert always
 * sends the FULL form, so a background write is identical to pressing Save
 * and switching tabs mid-edit no longer destroys input.
 */
import { useEffect, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import clsx from 'clsx'
import { Check, Plus } from 'lucide-react'

import Button from '../../../components/ui/Button'
import Card from '../../../components/ui/Card'
import Input, { FieldLabel } from '../../../components/ui/Input'
import QueryError from '../../../components/ui/QueryError'
import Select from '../../../components/ui/Select'
import { SkeletonCard } from '../../../components/ui/Skeleton'
import { getPreferences, upsertPreferences } from '../../../api/students'
import { DEGREE_OPTIONS, GEO_OPTIONS, nextIntakeTerms } from '../onboarding/catalog'
import { showToast } from '../../../stores/toast-store'
import { CITY_SIZE_OPTIONS } from '../../../utils/constants'
import { SaveStatus, SectionHeader, useAutosave } from './shared'

const PROGRAM_SIZE = [
  { value: 'small', label: 'Small' },
  { value: 'large', label: 'Large' },
  { value: 'no_preference', label: 'No preference' },
]
const RISK_LEVELS = [
  { value: 'conservative', label: 'Conservative' },
  { value: 'balanced', label: 'Balanced' },
  { value: 'ambitious', label: 'Ambitious' },
]
// Canonical pickers replacing free text — values mirror the onboarding catalog
// so what the student saves here maps to the same vocabulary Discover filters
// and the matcher already understand.
const DEGREE_LEVEL_OPTIONS = DEGREE_OPTIONS.map(d => ({ value: d.value, label: d.label }))
const START_TERM_OPTIONS = nextIntakeTerms().map(t => ({ value: t, label: t }))
const CLIMATE_OPTIONS = [
  { value: 'warm', label: 'Warm' },
  { value: 'four_seasons', label: 'Four seasons' },
  { value: 'cold', label: 'Cold' },
  { value: 'no_preference', label: 'No preference' },
]
const PROGRAM_STYLE_OPTIONS = [
  { value: 'research', label: 'Research-heavy' },
  { value: 'applied', label: 'Applied' },
  { value: 'balanced', label: 'Balanced' },
  { value: 'no_preference', label: 'No preference' },
]
// Region chips seed from the onboarding geo catalog; "Anywhere" is a guided
// answer there, not a storable place, so it's dropped from the picker.
const GEO_CHIPS = GEO_OPTIONS.filter(g => g !== 'Anywhere')

/** Chip-toggle multi-select — stores a string[] the API takes verbatim. */
function ChipMultiSelect({
  label,
  options,
  selected,
  onToggle,
}: {
  label: string
  options: string[]
  selected: string[]
  onToggle: (value: string) => void
}) {
  return (
    <div>
      <FieldLabel>{label}</FieldLabel>
      <div className="flex flex-wrap gap-1.5" role="group" aria-label={label}>
        {options.map(opt => {
          const on = selected.includes(opt)
          return (
            <button
              key={opt}
              type="button"
              aria-pressed={on}
              onClick={() => onToggle(opt)}
              className={clsx(
                'inline-flex items-center gap-1.5 rounded-pill border px-3 py-1.5 text-[13px] transition-colors duration-150',
                'focus:outline-none focus-visible:ring-2 focus-visible:ring-secondary/40',
                on
                  ? 'border-secondary bg-secondary/10 text-foreground'
                  : 'border-border bg-card text-muted-foreground hover:border-secondary/50 hover:text-foreground',
              )}
            >
              <span className={clsx('shrink-0', on ? 'text-secondary' : 'text-secondary/60')}>
                {on ? <Check size={13} /> : <Plus size={13} />}
              </span>
              {opt}
            </button>
          )
        })}
      </div>
    </div>
  )
}
const WEIGHTS: { key: string; label: string }[] = [
  { key: 'weight_cost', label: 'Cost' },
  { key: 'weight_location', label: 'Location' },
  { key: 'weight_outcomes', label: 'Career outcomes' },
  { key: 'weight_ranking', label: 'Prestige / ranking' },
  { key: 'weight_flexibility', label: 'Flexibility' },
  { key: 'weight_support', label: 'Support services' },
]

function WeightSlider({ label, value, onChange }: { label: string; value: number; onChange: (v: number) => void }) {
  return (
    <div>
      <div className="flex items-center justify-between mb-1">
        <span className="text-[13px] font-semibold text-muted-foreground">{label}</span>
        <span className="text-[13px] font-bold text-foreground tabular-nums">{value}</span>
      </div>
      <input
        type="range"
        min={0}
        max={10}
        value={value}
        onChange={e => onChange(Number(e.target.value))}
        className="w-full accent-[hsl(var(--secondary))]"
        aria-label={label}
      />
    </div>
  )
}

// Keep a previously-saved value visible even when it's outside the canonical
// list (a legacy free-text entry, or a start term that has since aged past the
// next-six window). Without this the native select would silently fall back to
// the placeholder and the round-trip would look like it lost the value.
const withCurrent = (
  options: { value: string; label: string }[],
  current: string | null | undefined,
): { value: string; label: string }[] =>
  current && !options.some(o => o.value === current)
    ? [...options, { value: current, label: current }]
    : options

// Cap parsed CSV lists so a pasted blob can't balloon the payload: at most
// 25 entries, each trimmed to 80 chars.
const splitCsv = (s: string): string[] =>
  s
    .split(',')
    .map(x => x.trim().slice(0, 80))
    .filter(Boolean)
    .slice(0, 25)

const toPayload = (form: any) => ({
  // Countries/regions are already canonical string[] from the chip pickers.
  preferred_countries: form.preferred_countries ?? [],
  preferred_regions: form.preferred_regions ?? [],
  preferred_city_size: form.preferred_city_size || null,
  preferred_climate: form.preferred_climate || null,
  program_size_preference: form.program_size_preference || null,
  target_degree_level: form.target_degree_level || null,
  target_start_term: form.target_start_term || null,
  preferred_program_style: form.preferred_program_style || null,
  risk_tolerance: form.risk_tolerance || null,
  dealbreakers: splitCsv(form.dealbreakers),
  weight_cost: form.weight_cost,
  weight_location: form.weight_location,
  weight_outcomes: form.weight_outcomes,
  weight_ranking: form.weight_ranking,
  weight_flexibility: form.weight_flexibility,
  weight_support: form.weight_support,
})

export default function PreferencesTab() {
  const qc = useQueryClient()
  const { data: prefs, isLoading, isError, refetch } = useQuery({ queryKey: ['preferences'], queryFn: getPreferences, retry: false })
  const [form, setForm] = useState<any>(null)
  // Set on the first user edit — gates autosave so the initial load (and any
  // background refetch) never triggers a write of untouched data.
  const [dirty, setDirty] = useState(false)

  useEffect(() => {
    // Initialize ONCE — later refetches (e.g. after an autosave invalidation)
    // must not clobber whatever the user is currently typing.
    if (prefs !== undefined && form === null) {
      const p: any = prefs ?? {}
      setForm({
        preferred_countries: p.preferred_countries ?? [],
        preferred_regions: p.preferred_regions ?? [],
        preferred_city_size: p.preferred_city_size ?? '',
        preferred_climate: p.preferred_climate ?? '',
        program_size_preference: p.program_size_preference ?? '',
        target_degree_level: p.target_degree_level ?? '',
        target_start_term: p.target_start_term ?? '',
        preferred_program_style: p.preferred_program_style ?? '',
        risk_tolerance: p.risk_tolerance ?? '',
        dealbreakers: (p.dealbreakers ?? []).join(', '),
        weight_cost: p.weight_cost ?? 5,
        weight_location: p.weight_location ?? 5,
        weight_outcomes: p.weight_outcomes ?? 5,
        weight_ranking: p.weight_ranking ?? 5,
        weight_flexibility: p.weight_flexibility ?? 5,
        weight_support: p.weight_support ?? 5,
      })
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [prefs])

  const saveMut = useMutation({
    mutationFn: upsertPreferences,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['preferences'] })
      qc.invalidateQueries({ queryKey: ['profile'] })
      showToast('Saved', 'success')
    },
    onError: () => showToast("Something didn't work. Try again.", 'error'),
  })

  // §19 autosave — debounced full-form upsert once the user has edited
  // anything; flushes on unmount so a quick tab switch can't destroy input.
  const autosaveState = useAutosave(
    form,
    async (f: any) => {
      if (!f) return
      await upsertPreferences(toPayload(f))
      qc.invalidateQueries({ queryKey: ['preferences'] })
      qc.invalidateQueries({ queryKey: ['profile'] })
    },
    { enabled: dirty && form !== null },
  )

  if (isError) return <QueryError onRetry={() => refetch()} />
  if (isLoading || !form) return <div className="space-y-3">{Array.from({ length: 2 }).map((_, i) => <SkeletonCard key={i} />)}</div>

  const set = (k: string, v: any) => {
    setDirty(true)
    setForm((f: any) => ({ ...f, [k]: v }))
  }
  const toggleInList = (k: string, value: string) => {
    setDirty(true)
    setForm((f: any) => {
      const cur: string[] = f[k] ?? []
      return { ...f, [k]: cur.includes(value) ? cur.filter(x => x !== value) : [...cur, value] }
    })
  }
  const save = () => saveMut.mutate(toPayload(form))

  return (
    <div className="space-y-8">
      <section>
        <SectionHeader title="Location & setting" description="Where you'd like to study." saveState={autosaveState} />
        <Card pad={false} className="p-5 space-y-5">
          <div className="grid sm:grid-cols-2 gap-x-4 gap-y-5">
            <ChipMultiSelect label="Preferred countries" options={GEO_CHIPS} selected={form.preferred_countries} onToggle={v => toggleInList('preferred_countries', v)} />
            <ChipMultiSelect label="Preferred regions" options={GEO_CHIPS} selected={form.preferred_regions} onToggle={v => toggleInList('preferred_regions', v)} />
          </div>
          <div className="grid sm:grid-cols-2 gap-x-4 gap-y-1">
            <Select label="City size" placeholder="No preference" options={CITY_SIZE_OPTIONS} value={form.preferred_city_size} onChange={e => set('preferred_city_size', e.target.value)} />
            <Select label="Climate" placeholder="No preference" options={withCurrent(CLIMATE_OPTIONS, form.preferred_climate)} value={form.preferred_climate} onChange={e => set('preferred_climate', e.target.value)} />
          </div>
        </Card>
      </section>

      <section>
        <SectionHeader title="Program" description="The shape of the program you're after." />
        <Card pad={false} className="p-5 grid sm:grid-cols-2 gap-x-4 gap-y-1">
          <Select label="Program size" placeholder="No preference" options={PROGRAM_SIZE} value={form.program_size_preference} onChange={e => set('program_size_preference', e.target.value)} />
          <Select label="Target degree level" placeholder="No preference" options={withCurrent(DEGREE_LEVEL_OPTIONS, form.target_degree_level)} value={form.target_degree_level} onChange={e => set('target_degree_level', e.target.value)} />
          <Select label="Target start term" placeholder="No preference" options={withCurrent(START_TERM_OPTIONS, form.target_start_term)} value={form.target_start_term} onChange={e => set('target_start_term', e.target.value)} />
          <Select label="Program style" placeholder="No preference" options={withCurrent(PROGRAM_STYLE_OPTIONS, form.preferred_program_style)} value={form.preferred_program_style} onChange={e => set('preferred_program_style', e.target.value)} />
          <Select label="Risk tolerance" placeholder="No preference" options={RISK_LEVELS} value={form.risk_tolerance} onChange={e => set('risk_tolerance', e.target.value)} />
          <Input label="Dealbreakers" placeholder="No online-only, …" value={form.dealbreakers} onChange={e => set('dealbreakers', e.target.value)} />
        </Card>
      </section>

      <section>
        <SectionHeader title="What matters most" description="Tune how strongly each factor weighs on your matches (0–10)." />
        <Card pad={false} className="p-5">
          <div className="grid sm:grid-cols-2 gap-x-8 gap-y-4">
            {WEIGHTS.map(w => (
              <WeightSlider key={w.key} label={w.label} value={form[w.key]} onChange={v => set(w.key, v)} />
            ))}
          </div>
        </Card>
      </section>

      <div className="flex items-center justify-end gap-3">
        <SaveStatus state={autosaveState} />
        <Button onClick={save} loading={saveMut.isPending}>Save preferences</Button>
      </div>
    </div>
  )
}
