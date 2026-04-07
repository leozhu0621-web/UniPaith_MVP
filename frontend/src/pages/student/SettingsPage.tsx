import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useAuthStore } from '../../stores/auth-store'
import { getNotificationPrefs, updateNotificationPrefs } from '../../api/notifications'
import Card from '../../components/ui/Card'
import Button from '../../components/ui/Button'
import { showToast } from '../../stores/toast-store'
import { useState, useEffect } from 'react'
import { formatDate } from '../../utils/format'

export default function SettingsPage() {
  const { user, logout } = useAuthStore()
  const queryClient = useQueryClient()
  const [emailEnabled, setEmailEnabled] = useState(true)
  const [prefs, setPrefs] = useState<Record<string, boolean>>({})

  const { data: notifPrefs } = useQuery({
    queryKey: ['notification-preferences'],
    queryFn: getNotificationPrefs,
  })

  useEffect(() => {
    if (notifPrefs) {
      setEmailEnabled(notifPrefs.email_enabled)
      setPrefs(notifPrefs.preferences || {})
    }
  }, [notifPrefs])

  const saveMut = useMutation({
    mutationFn: () => updateNotificationPrefs({ email_enabled: emailEnabled, preferences: prefs }),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['notification-preferences'] }); showToast('Preferences saved', 'success') },
  })

  const notifTypes = [
    { key: 'application_updates', label: 'Application updates' },
    { key: 'new_matches', label: 'New matches' },
    { key: 'messages', label: 'Messages' },
    { key: 'events', label: 'Marketing & events' },
  ]

  return (
    <div className="p-6 max-w-2xl mx-auto space-y-6">
      <h1 className="text-2xl font-semibold">Settings</h1>

      <Card className="p-5">
        <h2 className="font-semibold mb-3">Account</h2>
        <dl className="text-sm space-y-2">
          <div className="flex justify-between"><dt className="text-stone-500">Email</dt><dd>{user?.email}</dd></div>
          <div className="flex justify-between"><dt className="text-stone-500">Role</dt><dd className="capitalize">{user?.role?.replace(/_/g, ' ')}</dd></div>
          <div className="flex justify-between"><dt className="text-stone-500">Member since</dt><dd>{formatDate(user?.created_at)}</dd></div>
        </dl>
      </Card>

      <Card className="p-5">
        <h2 className="font-semibold mb-3">Notifications</h2>
        <div className="space-y-3">
          <label className="flex items-center gap-2 text-sm">
            <input type="checkbox" checked={emailEnabled} onChange={e => setEmailEnabled(e.target.checked)} />
            Email notifications enabled
          </label>
          {notifTypes.map(t => (
            <label key={t.key} className="flex items-center gap-2 text-sm ml-4">
              <input
                type="checkbox"
                checked={prefs[t.key] ?? true}
                onChange={e => setPrefs(p => ({ ...p, [t.key]: e.target.checked }))}
                disabled={!emailEnabled}
              />
              {t.label}
            </label>
          ))}
          <Button size="sm" onClick={() => saveMut.mutate()} loading={saveMut.isPending}>Save preferences</Button>
        </div>
      </Card>

      <Card className="p-5">
        <h2 className="font-semibold mb-3 text-red-600">Danger zone</h2>
        <Button variant="danger" onClick={logout}>Log out</Button>
      </Card>
    </div>
  )
}
