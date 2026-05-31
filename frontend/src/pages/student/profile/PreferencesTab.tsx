/**
 * Profile → Preferences tab (spec 10 §12).
 * Institution / program preferences + importance weights.
 */
import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { SlidersHorizontal } from 'lucide-react'

import { upsertPreferences } from '../../../api/students'
import Modal from '../../../components/ui/Modal'
import { SkeletonCard } from '../../../components/ui/Skeleton'
import { showToast } from '../../../stores/toast-store'
import { formatCurrency } from '../../../utils/format'
import { PreferencesForm } from '../components/ProfileForms'
import { EmptyHint, SectionCard, useProfile } from './_shared'

const WEIGHTS: { key: string; label: string }[] = [
  { key: 'weight_cost', label: 'Cost' },
  { key: 'weight_location', label: 'Location' },
  { key: 'weight_outcomes', label: 'Outcomes' },
  { key: 'weight_ranking', label: 'Ranking' },
  { key: 'weight_flexibility', label: 'Flexibility' },
  { key: 'weight_support', label: 'Support services' },
  { key: 'weight_time_to_degree', label: 'Time to degree' },
]

export default function PreferencesTab() {
  const qc = useQueryClient()
  const { data: p, isLoading } = useProfile()
  const [open, setOpen] = useState(false)

  const mut = useMutation({
    mutationFn: upsertPreferences,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['profile'] })
      qc.invalidateQueries({ queryKey: ['profile-overview'] })
      setOpen(false)
      showToast('Saved', 'success')
    },
    onError: () => showToast("Something didn't work. Try again.", 'error'),
  })

  if (isLoading) return <div className="space-y-4"><SkeletonCard /></div>
  const prefs: any = p?.preferences

  const rows: { label: string; value: string }[] = prefs
    ? [
        { label: 'Countries', value: prefs.preferred_countries?.join(', ') || '—' },
        { label: 'Regions', value: prefs.preferred_regions?.join(', ') || '—' },
        { label: 'City size', value: prefs.preferred_city_size || '—' },
        { label: 'Budget', value: prefs.budget_min != null ? `${formatCurrency(prefs.budget_min)} – ${formatCurrency(prefs.budget_max)}` : '—' },
        { label: 'Funding', value: prefs.funding_requirement || '—' },
        { label: 'Target degree', value: prefs.target_degree_level || '—' },
        { label: 'Start term', value: prefs.target_start_term || '—' },
        { label: 'Risk tolerance', value: prefs.risk_tolerance || '—' },
      ]
    : []

  const setWeights = WEIGHTS.filter(w => prefs?.[w.key] != null)

  return (
    <div className="space-y-6">
      <SectionCard title="Program preferences" icon={SlidersHorizontal} onEdit={() => setOpen(true)} lastUpdated={prefs?.updated_at}>
        {!prefs ? (
          <EmptyHint>No preferences set yet. These help match programs that fit your life.</EmptyHint>
        ) : (
          <dl className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-sm">
            {rows.map(r => (
              <div key={r.label}>
                <dt className="text-slate text-xs">{r.label}</dt>
                <dd className="text-charcoal">{r.value}</dd>
              </div>
            ))}
          </dl>
        )}
      </SectionCard>

      {setWeights.length > 0 && (
        <SectionCard title="What matters most" icon={SlidersHorizontal}>
          <div className="space-y-2">
            {setWeights.map(w => (
              <div key={w.key} className="flex items-center gap-3">
                <span className="text-sm text-charcoal w-32 shrink-0">{w.label}</span>
                <div className="flex-1 h-2 rounded-full bg-student-mist overflow-hidden">
                  <div className="h-full bg-cobalt" style={{ width: `${(Number(prefs[w.key]) / 10) * 100}%` }} />
                </div>
                <span className="text-xs text-slate tabular-nums w-8 text-right">{prefs[w.key]}/10</span>
              </div>
            ))}
          </div>
        </SectionCard>
      )}

      <Modal isOpen={open} onClose={() => setOpen(false)} title="Edit preferences" size="lg">
        <PreferencesForm defaultValues={prefs} loading={mut.isPending} onSubmit={d => mut.mutate(d)} />
      </Modal>
    </div>
  )
}
