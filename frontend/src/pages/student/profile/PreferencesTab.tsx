/**
 * Profile → Preferences tab (Spec/08 §12).
 * Structured pickers + importance weight sliders. Explicit Save (§10).
 */
import { useEffect, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import Button from '../../../components/ui/Button'
import Card from '../../../components/ui/Card'
import Input from '../../../components/ui/Input'
import QueryError from '../../../components/ui/QueryError'
import Select from '../../../components/ui/Select'
import { SkeletonCard } from '../../../components/ui/Skeleton'
import { getPreferences, upsertPreferences } from '../../../api/students'
import { showToast } from '../../../stores/toast-store'
import { CITY_SIZE_OPTIONS } from '../../../utils/constants'
import { SectionHeader } from './shared'

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

// Cap parsed CSV lists so a pasted blob can't balloon the payload: at most
// 25 entries, each trimmed to 80 chars.
const splitCsv = (s: string): string[] =>
  s
    .split(',')
    .map(x => x.trim().slice(0, 80))
    .filter(Boolean)
    .slice(0, 25)

export default function PreferencesTab() {
  const qc = useQueryClient()
  const { data: prefs, isLoading, isError, refetch } = useQuery({ queryKey: ['preferences'], queryFn: getPreferences, retry: false })
  const [form, setForm] = useState<any>(null)

  useEffect(() => {
    if (prefs !== undefined) {
      const p: any = prefs ?? {}
      setForm({
        preferred_countries: (p.preferred_countries ?? []).join(', '),
        preferred_regions: (p.preferred_regions ?? []).join(', '),
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

  if (isError) return <QueryError onRetry={() => refetch()} />
  if (isLoading || !form) return <div className="space-y-3">{Array.from({ length: 2 }).map((_, i) => <SkeletonCard key={i} />)}</div>

  const set = (k: string, v: any) => setForm((f: any) => ({ ...f, [k]: v }))
  const save = () => {
    saveMut.mutate({
      preferred_countries: splitCsv(form.preferred_countries),
      preferred_regions: splitCsv(form.preferred_regions),
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
  }

  return (
    <div className="space-y-8">
      <section>
        <SectionHeader title="Location & setting" description="Where you'd like to study." />
        <Card pad={false} className="p-5 grid sm:grid-cols-2 gap-x-4 gap-y-1">
          <Input label="Preferred countries" placeholder="United States, Canada" value={form.preferred_countries} onChange={e => set('preferred_countries', e.target.value)} />
          <Input label="Preferred regions" placeholder="Northeast, West Coast" value={form.preferred_regions} onChange={e => set('preferred_regions', e.target.value)} />
          <Select label="City size" placeholder="No preference" options={CITY_SIZE_OPTIONS} value={form.preferred_city_size} onChange={e => set('preferred_city_size', e.target.value)} />
          <Input label="Climate" placeholder="Mild, four seasons…" value={form.preferred_climate} onChange={e => set('preferred_climate', e.target.value)} />
        </Card>
      </section>

      <section>
        <SectionHeader title="Program" description="The shape of the program you're after." />
        <Card pad={false} className="p-5 grid sm:grid-cols-2 gap-x-4 gap-y-1">
          <Select label="Program size" placeholder="No preference" options={PROGRAM_SIZE} value={form.program_size_preference} onChange={e => set('program_size_preference', e.target.value)} />
          <Input label="Target degree level" placeholder="Master's, PhD…" value={form.target_degree_level} onChange={e => set('target_degree_level', e.target.value)} />
          <Input label="Target start term" placeholder="Fall 2027" value={form.target_start_term} onChange={e => set('target_start_term', e.target.value)} />
          <Input label="Program style" placeholder="Research-heavy, applied…" value={form.preferred_program_style} onChange={e => set('preferred_program_style', e.target.value)} />
          <Select label="Risk tolerance" placeholder="Select…" options={RISK_LEVELS} value={form.risk_tolerance} onChange={e => set('risk_tolerance', e.target.value)} />
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

      <div className="flex justify-end">
        <Button onClick={save} loading={saveMut.isPending}>Save preferences</Button>
      </div>
    </div>
  )
}
