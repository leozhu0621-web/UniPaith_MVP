import { useEffect, useState } from 'react'
import { Bell, Lock } from 'lucide-react'
import Toggle from '../../../components/ui/Toggle'
import Select from '../../../components/ui/Select'
import SettingsSection, { SettingRow } from './SettingsSection'
import { updateNotificationPrefs } from '../../../api/notifications'
import { showToast } from '../../../stores/toast-store'
import type {
  EmailFrequency,
  NotificationChannelKey,
  NotificationChannels,
  NotificationTypePref,
} from '../../../types'

const CHANNELS: { key: NotificationChannelKey; label: string; tip?: string }[] = [
  { key: 'email', label: 'Email' },
  { key: 'sms', label: 'SMS' },
  { key: 'in_app', label: 'In-app' },
  { key: 'push', label: 'Push' },
]

const FREQUENCIES: { value: EmailFrequency; label: string }[] = [
  { value: 'all', label: 'All emails' },
  { value: 'weekly', label: 'Weekly digest' },
  { value: 'important', label: 'Important only' },
  { value: 'none', label: 'None' },
]

interface NotificationsCardProps {
  notifications: NotificationTypePref[]
  emailEnabled: boolean
  emailFrequency: EmailFrequency
  onChanged?: () => void
}

function toPrefsDict(rows: NotificationTypePref[]): Record<string, NotificationChannels> {
  return Object.fromEntries(rows.map(r => [r.type, r.channels]))
}

export default function NotificationsCard({
  notifications,
  emailEnabled,
  emailFrequency,
  onChanged,
}: NotificationsCardProps) {
  const [rows, setRows] = useState<NotificationTypePref[]>(notifications)
  const [emailOn, setEmailOn] = useState(emailEnabled)
  const [freq, setFreq] = useState<EmailFrequency>(emailFrequency)
  const [saving, setSaving] = useState(false)

  useEffect(() => setRows(notifications), [notifications])
  useEffect(() => setEmailOn(emailEnabled), [emailEnabled])
  useEffect(() => setFreq(emailFrequency), [emailFrequency])

  const persist = async (next: {
    rows?: NotificationTypePref[]
    emailOn?: boolean
    freq?: EmailFrequency
  }) => {
    const prevRows = rows
    const prevEmailOn = emailOn
    const prevFreq = freq
    if (next.rows) setRows(next.rows)
    if (next.emailOn !== undefined) setEmailOn(next.emailOn)
    if (next.freq) setFreq(next.freq)
    setSaving(true)
    try {
      await updateNotificationPrefs({
        email_enabled: next.emailOn ?? emailOn,
        email_frequency: next.freq ?? freq,
        preferences: toPrefsDict(next.rows ?? rows),
      })
      onChanged?.()
    } catch (e) {
      // revert on failure
      setRows(prevRows)
      setEmailOn(prevEmailOn)
      setFreq(prevFreq)
      showToast(e instanceof Error ? e.message : 'Could not save notifications', 'error')
    } finally {
      setSaving(false)
    }
  }

  const toggleChannel = (type: string, ch: NotificationChannelKey, value: boolean) => {
    const next = rows.map(r =>
      r.type === type ? { ...r, channels: { ...r.channels, [ch]: value } } : r
    )
    persist({ rows: next })
  }

  return (
    <SettingsSection
      icon={Bell}
      title="Notifications"
      description="Choose how each kind of update reaches you. Essential application alerts always stay in-app."
    >
      <SettingRow label="Email notifications" description="Master switch for all email.">
        <Toggle
          checked={emailOn}
          onChange={v => persist({ emailOn: v })}
          label="Email notifications"
          disabled={saving}
        />
      </SettingRow>

      <div className="overflow-x-auto -mx-1 px-1">
        <div className="min-w-[460px]">
          {/* header */}
          <div className="grid grid-cols-[1fr_repeat(4,52px)] items-end gap-x-1 pb-2 border-b border-border">
            <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">
              Type
            </span>
            {CHANNELS.map(c => (
              <span key={c.key} className="text-[11px] font-semibold text-muted-foreground text-center">
                {c.label}
              </span>
            ))}
          </div>
          {/* rows */}
          {rows.map(row => (
            <div
              key={row.type}
              className="grid grid-cols-[1fr_repeat(4,52px)] items-center gap-x-1 py-2.5 border-b border-border/60 last:border-0"
            >
              <span className="text-sm text-foreground flex items-center gap-1.5 pr-2">
                {row.label}
                {row.essential && (
                  <span title="Essential — in-app can't be turned off">
                    <Lock size={12} className="text-muted-foreground shrink-0" />
                  </span>
                )}
              </span>
              {CHANNELS.map(c => {
                const locked = row.essential && c.key === 'in_app'
                return (
                  <div key={c.key} className="flex justify-center">
                    <Toggle
                      size="sm"
                      checked={row.channels[c.key]}
                      onChange={v => toggleChannel(row.type, c.key, v)}
                      disabled={saving || locked || (c.key === 'email' && !emailOn)}
                      label={`${row.label} via ${c.label}`}
                    />
                  </div>
                )
              })}
            </div>
          ))}
        </div>
      </div>

      <div className="border-t border-border mt-1 pt-2">
        <SettingRow label="Email frequency" description="How often we batch non-urgent email.">
          <div className="w-44">
            <Select
              uiSize="sm"
              options={FREQUENCIES}
              value={freq}
              onChange={e => persist({ freq: e.target.value as EmailFrequency })}
              disabled={saving || !emailOn}
            />
          </div>
        </SettingRow>
      </div>
    </SettingsSection>
  )
}
