import { useEffect, useState } from 'react'
import { ClipboardCheck } from 'lucide-react'
import Toggle from '../../../components/ui/Toggle'
import Select from '../../../components/ui/Select'
import SettingsSection, { SettingRow } from '../../student/settings/SettingsSection'
import { updateInstitutionSettings, type UpdateInstitutionSettingsPayload } from '../../../api/settings'
import { showToast } from '../../../stores/toast-store'
import type { ReviewConfig } from '../../../types'

const ASSIGNMENT_MODES = [
  { value: 'round_robin', label: 'Round robin' },
  { value: 'load_balanced', label: 'Load balanced' },
  { value: 'manual', label: 'Manual only' },
]

interface ReviewConfigCardProps {
  config: ReviewConfig
  onChanged: () => void
}

export default function ReviewConfigCard({ config, onChanged }: ReviewConfigCardProps) {
  const [blind, setBlind] = useState(config.blind_review_default)
  const [calibration, setCalibration] = useState(config.calibration_enabled)
  const [mode, setMode] = useState(config.reviewer_assignment_mode)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    setBlind(config.blind_review_default)
    setCalibration(config.calibration_enabled)
    setMode(config.reviewer_assignment_mode)
  }, [config])

  const persist = async (patch: UpdateInstitutionSettingsPayload) => {
    setSaving(true)
    try {
      await updateInstitutionSettings(patch)
      onChanged()
    } catch (e) {
      showToast(e instanceof Error ? e.message : 'Could not save review settings', 'error')
    } finally {
      setSaving(false)
    }
  }

  return (
    <SettingsSection
      icon={ClipboardCheck}
      title="Review configuration"
      description="Blind review defaults, reader calibration, and how reviewers are assigned."
    >
      <SettingRow
        label="Blind review by default"
        description="Redact identity-revealing fields during scoring (Spec 32 §7A.1)."
      >
        <Toggle
          checked={blind}
          disabled={saving}
          onChange={v => {
            setBlind(v)
            persist({ review_config: { blind_review_default: v } })
          }}
          label="Blind review default"
        />
      </SettingRow>
      <SettingRow
        label="Reader calibration"
        description="Enable calibration sets and inter-rater reliability tracking (§7A.2)."
      >
        <Toggle
          checked={calibration}
          disabled={saving}
          onChange={v => {
            setCalibration(v)
            persist({ review_config: { calibration_enabled: v } })
          }}
          label="Calibration enabled"
        />
      </SettingRow>
      <SettingRow
        label="Reviewer assignment"
        description="Default strategy when new applications enter the review queue."
      >
        <div className="w-44">
          <Select
            uiSize="sm"
            options={ASSIGNMENT_MODES}
            value={mode}
            disabled={saving}
            onChange={e => {
              const next = e.target.value as ReviewConfig['reviewer_assignment_mode']
              setMode(next)
              persist({ review_config: { reviewer_assignment_mode: next } })
            }}
          />
        </div>
      </SettingRow>
    </SettingsSection>
  )
}
