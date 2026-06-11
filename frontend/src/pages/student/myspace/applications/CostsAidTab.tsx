/**
 * My Space › Applications › Costs & aid (Spec 2026-06-10 §5).
 * Moved from Profile › Financial: budget band + funding intent (writes to
 * preferences) + the cost-comparison surface — plus the scholarship matcher
 * (Spec 70 §3), surfaced in the UI for the first time.
 */
import { lazy, Suspense, useEffect, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Award } from 'lucide-react'

import Button from '../../../../components/ui/Button'
import Card from '../../../../components/ui/Card'
import Badge from '../../../../components/ui/Badge'
import Input from '../../../../components/ui/Input'
import QueryError from '../../../../components/ui/QueryError'
import Select from '../../../../components/ui/Select'
import { SkeletonCard } from '../../../../components/ui/Skeleton'
import { getPreferences, upsertPreferences, getScholarshipMatches } from '../../../../api/students'
import { showToast } from '../../../../stores/toast-store'
import { formatCurrency } from '../../../../utils/format'
import { FUNDING_OPTIONS } from '../../../../utils/constants'
import { SectionHeader } from '../../profile/shared'

const FinancialAidPage = lazy(() => import('../../FinancialAidPage'))

export default function CostsAidTab() {
  const qc = useQueryClient()
  const { data: prefs, isLoading, isError, refetch } = useQuery({ queryKey: ['preferences'], queryFn: getPreferences, retry: false })
  const scholarships = useQuery({ queryKey: ['scholarship-matches'], queryFn: () => getScholarshipMatches(10), retry: false })
  const [form, setForm] = useState<any>(null)

  useEffect(() => {
    if (prefs !== undefined) {
      const p: any = prefs ?? {}
      setForm({
        budget_min: p.budget_min ?? '',
        budget_max: p.budget_max ?? '',
        funding_requirement: p.funding_requirement ?? '',
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
  if (isLoading || !form) return <div className="space-y-3"><SkeletonCard /></div>

  const set = (k: string, v: any) => setForm((f: any) => ({ ...f, [k]: v }))
  const save = () => {
    const min = form.budget_min === '' ? null : Number(form.budget_min)
    const max = form.budget_max === '' ? null : Number(form.budget_max)
    if ((min != null && (Number.isNaN(min) || min < 0)) || (max != null && (Number.isNaN(max) || max < 0))) {
      showToast('Budget amounts must be zero or greater.', 'error')
      return
    }
    if (min != null && max != null && min > max) {
      showToast('Minimum budget must be less than or equal to the maximum.', 'error')
      return
    }
    saveMut.mutate({
      budget_min: min,
      budget_max: max,
      funding_requirement: form.funding_requirement || null,
    })
  }

  const band =
    form.funding_requirement === 'full_scholarship'
      ? { label: 'Aid-dependent', tone: 'text-warning' }
      : form.funding_requirement === 'self_funded'
        ? { label: 'Self-funded', tone: 'text-success' }
        : { label: 'Mixed funding', tone: 'text-secondary' }

  const matchList = Array.isArray(scholarships.data) ? scholarships.data : []

  return (
    <div className="space-y-8">
      <section>
        <SectionHeader title="Budget & funding" description="Your annual ceiling and how you plan to fund it." />
        <Card className="p-5 space-y-4">
          <div className="grid sm:grid-cols-2 gap-x-4 gap-y-1">
            <Input label="Annual budget — minimum (USD)" type="number" min={0} placeholder="0" value={form.budget_min} onChange={e => set('budget_min', e.target.value)} />
            <Input label="Annual budget — maximum (USD)" type="number" min={0} placeholder="50000" value={form.budget_max} onChange={e => set('budget_max', e.target.value)} />
          </div>
          <div className="max-w-xs">
            <Select label="Funding plan" placeholder="Select…" options={FUNDING_OPTIONS} value={form.funding_requirement} onChange={e => set('funding_requirement', e.target.value)} />
          </div>
          {(form.budget_min || form.budget_max) && (
            <p className="text-sm text-muted-foreground">
              Targeting{' '}
              <span className="font-semibold text-foreground">
                {formatCurrency(Number(form.budget_min) || 0)}–{formatCurrency(Number(form.budget_max) || 0)}
              </span>{' '}
              per year · <span className={`font-semibold ${band.tone}`}>{band.label}</span>
            </p>
          )}
          <div className="flex justify-end">
            <Button onClick={save} loading={saveMut.isPending}>Save</Button>
          </div>
        </Card>
      </section>

      {/* Scholarship matcher (Spec 70 §3) — deterministic, profile-driven. */}
      <section>
        <SectionHeader title="Scholarships you may qualify for" description="Matched from your profile — a verified mismatch excludes an award, an unknown field never does." />
        {scholarships.isLoading ? (
          <SkeletonCard />
        ) : scholarships.isError ? (
          <QueryError variant="inline" detail="We couldn't load scholarship matches." onRetry={() => scholarships.refetch()} />
        ) : matchList.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            No matches yet — completing your profile (academics, identity, goals) unlocks more awards.
          </p>
        ) : (
          <div className="space-y-2">
            {matchList.map(s => (
              <div key={s.scholarship_id} className="flex items-center justify-between gap-3 rounded-lg border border-border bg-card px-3 py-2.5">
                <div className="min-w-0 flex items-start gap-2.5">
                  <Award size={15} className="mt-0.5 shrink-0 text-secondary" />
                  <div className="min-w-0">
                    <p className="truncate text-sm font-medium text-foreground">{s.name}</p>
                    {s.reasons.length > 0 && (
                      <p className="truncate text-xs text-muted-foreground">{s.reasons.join(' · ')}</p>
                    )}
                  </div>
                </div>
                <div className="flex shrink-0 items-center gap-2">
                  <Badge variant="neutral">{s.scholarship_type.replace(/_/g, ' ')}</Badge>
                  <span className="text-sm font-semibold text-foreground">{formatCurrency(s.award_estimate)}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      <section>
        <SectionHeader title="Cost comparison" description="Estimate and compare net cost across your saved and applied programs." />
        <Suspense fallback={<SkeletonCard />}>
          <FinancialAidPage />
        </Suspense>
      </section>
    </div>
  )
}
