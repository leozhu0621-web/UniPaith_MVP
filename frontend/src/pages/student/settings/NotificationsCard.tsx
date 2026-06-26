import { useEffect, useState } from 'react'
import { Bell, Lock } from 'lucide-react'
import Toggle from '../../../components/ui/Toggle'
import SettingsSection from './SettingsSection'
import { updateNotificationPrefs } from '../../../api/notifications'
import { showToast } from '../../../stores/toast-store'
import type {
  EmailFrequency,
  NotificationChannels,
  NotificationTypePref,
} from '../../../types'

interface NotificationsCardProps {
  notifications: NotificationTypePref[]
  // Accepted for back-compat with the settings page; email is dropped so these
  // are no longer rendered.
  emailEnabled?: boolean
  emailFrequency?: EmailFrequency
  onChanged?: () => void
}

function toPrefsDict(rows: NotificationTypePref[]): Record<string, NotificationChannels> {
  return Object.fromEntries(rows.map(r => [r.type, r.channels]))
}

/**
 * Notifications are IN-APP ONLY. Email / SMS / push were dropped to keep the app
 * simple — the email-frequency and SMS/push controls never actually delivered.
 * The card persists email off and lets the student pick which updates show in-app
 * (essential ones are always on).
 */
export default function NotificationsCard({ notifications, onChanged }: NotificationsCardProps) {
  const [rows, setRows] = useState<NotificationTypePref[]>(notifications)
  const [saving, setSaving] = useState(false)

  useEffect(() => setRows(notifications), [notifications])

  const persist = async (nextRows: NotificationTypePref[]) => {
    const prevRows = rows
    setRows(nextRows)
    setSaving(true)
    try {
      await updateNotificationPrefs({
        email_enabled: false,
        email_frequency: 'none',
        preferences: toPrefsDict(nextRows),
      })
      onChanged?.()
    } catch (e) {
      setRows(prevRows)
      showToast(e instanceof Error ? e.message : 'Could not save notifications', 'error')
    } finally {
      setSaving(false)
    }
  }

  const toggleInApp = (type: string, value: boolean) => {
    persist(
      rows.map(r => (r.type === type ? { ...r, channels: { ...r.channels, in_app: value } } : r)),
    )
  }

  return (
    <SettingsSection icon={Bell} title="Notifications">
      <p className="mb-2 text-xs text-muted-foreground">
        Notifications appear in the app. Choose which updates you want to see.
      </p>
      <div>
        {rows.map(row => {
          const locked = row.essential // essential notifications can't be turned off
          return (
            <div
              key={row.type}
              className="flex items-center justify-between gap-3 border-b border-border/60 py-2.5 last:border-0"
            >
              <span className="flex items-center gap-1.5 text-sm text-foreground">
                {row.label}
                {row.essential && (
                  <span title="Essential — can't be turned off">
                    <Lock size={12} className="shrink-0 text-muted-foreground" />
                  </span>
                )}
              </span>
              <Toggle
                size="sm"
                checked={locked ? true : row.channels.in_app}
                onChange={v => toggleInApp(row.type, v)}
                disabled={saving || locked}
                label={`${row.label} in-app`}
              />
            </div>
          )
        })}
      </div>
    </SettingsSection>
  )
}
