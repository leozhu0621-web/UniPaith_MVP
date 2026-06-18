import { useEffect, useState } from 'react'
import { Sparkles, ShieldOff } from 'lucide-react'
import Toggle from '../../../components/ui/Toggle'
import AIBadge from '../../../components/ui/AIBadge'
import SettingsSection, { SettingRow } from '../../student/settings/SettingsSection'
import { updateInstitutionSettings, type UpdateInstitutionSettingsPayload } from '../../../api/settings'
import { showToast } from '../../../stores/toast-store'
import type { AIConfig } from '../../../types'

// Canonical institution AI surfaces (mirrors services/ai_config_service.AI_SURFACES).
// `confidence: true` surfaces expose a per-surface threshold slider (Spec 37 §5).
const SURFACE_META: { key: string; label: string; confidence: boolean }[] = [
  { key: 'packet_summary', label: 'AI packet summary', confidence: false },
  { key: 'rubric_prefill', label: 'Rubric pre-fill', confidence: true },
  { key: 'assistant_chat', label: 'Applicant assistant chat', confidence: false },
  { key: 'message_draft', label: 'AI message drafts', confidence: false },
  { key: 'authenticity_risk', label: 'Authenticity risk scoring', confidence: true },
  { key: 'intelligence_digest', label: 'Intelligence digest', confidence: false },
  { key: 'doc_parse_triage', label: 'Document parse triage', confidence: false },
  { key: 'campaign_copy', label: 'Campaign copy suggestions', confidence: false },
]

interface AIConfigCardProps {
  config: AIConfig
  onChanged: () => void
}

export default function AIConfigCard({ config, onChanged }: AIConfigCardProps) {
  const [local, setLocal] = useState<AIConfig>(config)
  const [saving, setSaving] = useState(false)

  useEffect(() => setLocal(config), [config])

  const persist = async (patch: UpdateInstitutionSettingsPayload) => {
    setSaving(true)
    try {
      await updateInstitutionSettings(patch)
      onChanged()
    } catch (e) {
      showToast(e instanceof Error ? e.message : 'Could not save AI settings', 'error')
    } finally {
      setSaving(false)
    }
  }

  const setEnabled = (key: string, enabled: boolean) => {
    setLocal(c => ({ ...c, surfaces: { ...c.surfaces, [key]: { ...c.surfaces[key], enabled } } }))
    persist({ ai_config: { surfaces: { [key]: { enabled } } } })
  }

  const setThresholdLocal = (key: string, min_confidence: number) =>
    setLocal(c => ({ ...c, surfaces: { ...c.surfaces, [key]: { ...c.surfaces[key], min_confidence } } }))

  const commitThreshold = (key: string, min_confidence: number) =>
    persist({ ai_config: { surfaces: { [key]: { min_confidence } } } })

  return (
    <div className="space-y-5">
      <SettingsSection
        icon={Sparkles}
        title="AI-assistive features"
        action={<AIBadge label="AI assist" />}
      >
        {SURFACE_META.map(s => {
          const sc = local.surfaces[s.key] ?? { enabled: true, min_confidence: 0 }
          return (
            <SettingRow key={s.key} label={s.label}>
              <div className="flex flex-col items-end gap-2">
                <Toggle
                  checked={sc.enabled}
                  disabled={saving}
                  onChange={v => setEnabled(s.key, v)}
                  label={`${s.label} enabled`}
                />
                {s.confidence && sc.enabled && (
                  <label className="flex items-center gap-2 text-xs text-muted-foreground">
                    <span className="whitespace-nowrap">Min confidence</span>
                    <input
                      type="range"
                      min={0}
                      max={100}
                      step={5}
                      value={sc.min_confidence}
                      disabled={saving}
                      onChange={e => setThresholdLocal(s.key, Number(e.target.value))}
                      onPointerUp={e => commitThreshold(s.key, Number((e.target as HTMLInputElement).value))}
                      onKeyUp={e => commitThreshold(s.key, Number((e.target as HTMLInputElement).value))}
                      className="h-1 w-28 cursor-pointer accent-secondary"
                      aria-label={`${s.label} minimum confidence`}
                    />
                    <span className="w-8 text-right tabular-nums font-medium text-foreground">{sc.min_confidence}</span>
                  </label>
                )}
              </div>
            </SettingRow>
          )
        })}
      </SettingsSection>

      <SettingsSection icon={ShieldOff} title="Data & training">
        <SettingRow label="No-training tier">
          <Toggle
            checked={local.no_training}
            disabled={saving}
            onChange={v => {
              setLocal(c => ({ ...c, no_training: v }))
              persist({ ai_config: { no_training: v } })
            }}
            label="No-training tier"
          />
        </SettingRow>
      </SettingsSection>
    </div>
  )
}
