/**
 * Profile → Financial tab (spec 10 §13).
 * Budget band + funding intent (from preferences / visa) + the live cost
 * calculator (FinancialAidPage). Kept separate from Preferences per spec §22.
 */
import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { PiggyBank } from 'lucide-react'

import { upsertPreferences } from '../../../api/students'
import Card from '../../../components/ui/Card'
import Modal from '../../../components/ui/Modal'
import { SkeletonCard } from '../../../components/ui/Skeleton'
import { showToast } from '../../../stores/toast-store'
import { formatCurrency } from '../../../utils/format'
import { PreferencesForm } from '../components/ProfileForms'
import FinancialAidPage from '../FinancialAidPage'
import { SectionCard, useProfile } from './_shared'

export default function FinancialTab() {
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
  const visa: any = p?.visa_info

  const rows = [
    { label: 'Annual budget', value: prefs?.budget_min != null ? `${formatCurrency(prefs.budget_min)} – ${formatCurrency(prefs.budget_max)}` : 'Not set' },
    { label: 'Funding need', value: prefs?.funding_requirement || 'Not set' },
    { label: 'Financial proof', value: visa?.financial_proof_available ? (visa.financial_proof_amount_band || 'Available') : 'Not provided' },
    { label: 'Sponsorship', value: visa?.sponsorship_source || 'None' },
  ]

  return (
    <div className="space-y-6">
      <SectionCard title="Budget & funding" icon={PiggyBank} onEdit={() => setOpen(true)} lastUpdated={prefs?.updated_at}>
        <dl className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-sm">
          {rows.map(r => (
            <div key={r.label}>
              <dt className="text-slate text-xs">{r.label}</dt>
              <dd className="text-charcoal">{r.value}</dd>
            </div>
          ))}
        </dl>
      </SectionCard>

      <Card className="p-0 overflow-hidden">
        <FinancialAidPage />
      </Card>

      <Modal isOpen={open} onClose={() => setOpen(false)} title="Edit budget & funding" size="lg">
        <PreferencesForm defaultValues={prefs} loading={mut.isPending} onSubmit={d => mut.mutate(d)} />
      </Modal>
    </div>
  )
}
