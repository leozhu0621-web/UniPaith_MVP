/**
 * Spec 46 §9/§10/§1/§5 — institution Data & Privacy settings.
 * Mounted at /i/settings?tab=data. Governance config (override expiry,
 * protected attributes, no-training tier) + the sub-processor list (§10) +
 * the verbatim brand commitments (§1) + the retention schedule (§5).
 */
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Database, ShieldCheck, Scale, Server, Clock, Sparkles } from 'lucide-react'

import Button from '../../../components/ui/Button'
import Select from '../../../components/ui/Select'
import Toggle from '../../../components/ui/Toggle'
import { SkeletonCard } from '../../../components/ui/Skeleton'
import SettingsSection, { SettingRow } from '../../student/settings/SettingsSection'
import { getDataGovernance, updateDataGovernance } from '../../../api/fairness'
import type { DataGovernanceSettings } from '../../../types/fairness'
import { showToast } from '../../../stores/toast-store'

const ATTR_LABEL: Record<string, string> = {
  race: 'Race / ethnicity',
  gender: 'Gender identity',
  first_gen: 'First-generation',
  international: 'International',
  nationality_region: 'Nationality region',
  disability: 'Disability',
  veteran: 'Veteran',
}
const ALL_ATTRS = [
  'race',
  'gender',
  'first_gen',
  'international',
  'nationality_region',
  'disability',
  'veteran',
]

export default function DataGovernanceCard() {
  const qc = useQueryClient()
  const { data, isLoading } = useQuery({
    queryKey: ['data-governance'],
    queryFn: getDataGovernance,
    retry: false,
  })

  const save = useMutation({
    mutationFn: (patch: Partial<DataGovernanceSettings>) => updateDataGovernance(patch),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['data-governance'] })
      showToast('Saved', 'success')
    },
    onError: (e: any) => showToast(e?.message || 'Save failed', 'error'),
  })

  if (isLoading || !data) {
    return (
      <div className="space-y-3">
        <SkeletonCard />
        <SkeletonCard />
      </div>
    )
  }

  const s = data.settings
  const tracked = new Set(s.protected_attributes_tracked)
  const toggleAttr = (attr: string, on: boolean) => {
    const next = new Set(tracked)
    if (on) next.add(attr)
    else next.delete(attr)
    save.mutate({ protected_attributes_tracked: Array.from(next) })
  }

  return (
    <div className="space-y-6">
      {/* §1 — the brand commitments (verbatim, contractual). */}
      <SettingsSection
        icon={ShieldCheck}
        title="Our commitments"
        description="The contractual promises behind every match and every score."
      >
        <div className="grid gap-3 sm:grid-cols-2">
          {data.brand_commitments.map(c => (
            <div key={c.title} className="rounded-lg border border-border p-3">
              <p className="text-sm font-semibold text-foreground">{c.title}</p>
              <p className="text-xs text-muted-foreground mt-1">{c.body}</p>
            </div>
          ))}
        </div>
        <p className="text-xs text-muted-foreground mt-3">{data.no_data_sale}</p>
      </SettingsSection>

      {/* §6/§9 — fairness governance. */}
      <SettingsSection
        icon={Scale}
        title="Fairness governance"
        description="How disparate-impact auto-halts behave for your programs (§6 / §9)."
      >
        <SettingRow
          label="Default override expiry"
          description="How long a logged override lifts a halt before it re-arms."
        >
          <Select
            value={String(s.override_expiry_weeks_default)}
            onChange={e => save.mutate({ override_expiry_weeks_default: Number(e.target.value) })}
            options={[
              { value: '1', label: '1 week' },
              { value: '2', label: '2 weeks' },
              { value: '3', label: '3 weeks' },
              { value: '4', label: '4 weeks (max)' },
            ]}
          />
        </SettingRow>

        <div className="py-2.5 border-t border-border">
          <p className="text-sm font-medium text-foreground">Protected attributes tracked</p>
          <p className="text-xs text-muted-foreground mt-0.5 mb-2">
            Disable an attribute your institution doesn't collect. Disabled attributes are never
            scored for disparate impact.
          </p>
          <div className="space-y-1">
            {ALL_ATTRS.map(attr => (
              <SettingRow key={attr} label={ATTR_LABEL[attr] ?? attr}>
                <Toggle
                  label={ATTR_LABEL[attr] ?? attr}
                  checked={tracked.has(attr)}
                  disabled={save.isPending}
                  onChange={v => toggleAttr(attr, v)}
                />
              </SettingRow>
            ))}
          </div>
        </div>

        {data.program_thresholds.length > 0 && (
          <div className="py-2.5 border-t border-border">
            <p className="text-sm font-medium text-foreground mb-1">Per-program thresholds</p>
            <div className="space-y-1">
              {data.program_thresholds.map(p => (
                <div key={p.program_id} className="flex items-center justify-between text-sm py-1">
                  <span className="text-foreground">{p.program_name}</span>
                  <span className="tabular-nums text-muted-foreground">
                    Δ &gt; {p.fairness_threshold.toFixed(2)}
                    {p.matching_halted && <span className="text-error ml-2">· halted</span>}
                  </span>
                </div>
              ))}
            </div>
            <p className="text-xs text-muted-foreground mt-2">
              Tune individual thresholds on the{' '}
              <a href="/i/admissions?tab=fairness" className="text-secondary underline-offset-2 hover:underline">
                Fairness page
              </a>
              .
            </p>
          </div>
        )}
      </SettingsSection>

      {/* §9 — no-training tier + residency. */}
      <SettingsSection
        icon={Sparkles}
        title="Model training & residency"
        description="Control whether your applicants' data may ever train a UniPaith model."
      >
        <SettingRow
          label="No-training tier"
          description="Force consent.training = false for your program data, overriding per-student consent. Anthropic does not train on customer data by default."
        >
          <Toggle
            label="No-training tier"
            checked={s.no_training_tier}
            disabled={save.isPending}
            onChange={v => save.mutate({ no_training_tier: v })}
          />
        </SettingRow>
        <SettingRow
          label="Data residency"
          description="Where production data is hosted. Multi-region is a future phase — US only today."
        >
          <Select
            value={s.data_residency}
            onChange={e => save.mutate({ data_residency: e.target.value })}
            options={[
              { value: 'us', label: 'United States' },
              { value: 'canada', label: 'Canada (planned)' },
              { value: 'eu', label: 'EU (planned)' },
            ]}
          />
        </SettingRow>
      </SettingsSection>

      {/* §10 — sub-processor list. */}
      <SettingsSection
        icon={Server}
        title="Sub-processors"
        description="The vendors that touch data on UniPaith's behalf, and what each one touches (§10)."
      >
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-xs uppercase tracking-wide text-muted-foreground bg-muted">
                <th className="px-3 py-2 font-semibold rounded-l-lg">Sub-processor</th>
                <th className="px-3 py-2 font-semibold">What it touches</th>
                <th className="px-3 py-2 font-semibold">Classification</th>
                <th className="px-3 py-2 font-semibold rounded-r-lg">Region</th>
              </tr>
            </thead>
            <tbody>
              {data.subprocessors.map(sp => (
                <tr key={sp.name} className="border-t border-border align-top">
                  <td className="px-3 py-2 text-foreground font-medium">{sp.name}</td>
                  <td className="px-3 py-2 text-muted-foreground">{sp.touches}</td>
                  <td className="px-3 py-2 text-muted-foreground">{sp.classification}</td>
                  <td className="px-3 py-2 text-muted-foreground whitespace-nowrap">{sp.region}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="text-xs text-muted-foreground mt-3">{data.subprocessor_note}</p>
      </SettingsSection>

      {/* §5 — retention schedule. */}
      <SettingsSection
        icon={Clock}
        title="Data retention"
        description="How long each class of data is kept (§5)."
      >
        <div className="divide-y divide-border">
          {data.retention_policy.map(r => (
            <div key={r.data_type} className="flex items-start justify-between gap-4 py-2">
              <span className="text-sm font-medium text-foreground">{r.data_type}</span>
              <span className="text-sm text-muted-foreground text-right max-w-[60%]">{r.retention}</span>
            </div>
          ))}
        </div>
      </SettingsSection>

      {/* §9 — institution funnel export reuses the analytics export. */}
      <SettingsSection
        icon={Database}
        title="Export your data"
        description="Download your own funnel — applicants, engagement, and outcomes."
      >
        <div className="flex gap-2">
          <Button
            size="sm"
            variant="tertiary"
            onClick={() =>
              window.open('/i/analytics?export=csv', '_self')
            }
          >
            Open analytics export
          </Button>
        </div>
      </SettingsSection>
    </div>
  )
}
