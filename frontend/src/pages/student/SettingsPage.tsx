import { useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getSettings, updateSettings, type UpdateSettingsPayload } from '../../api/settings'
import { useThemeStore, type FontSize, type Theme } from '../../stores/theme-store'
import { showToast } from '../../stores/toast-store'
import AccountCard from './settings/AccountCard'
import SecurityCard from './settings/SecurityCard'
import PreferencesCard from './settings/PreferencesCard'
import NotificationsCard from './settings/NotificationsCard'
import ConnectCard from './settings/ConnectCard'
import DataPrivacyCard from './settings/DataPrivacyCard'
import BillingCard from './settings/BillingCard'
import SignOutCard from './settings/SignOutCard'
import DangerZone from './settings/DangerZone'

export default function SettingsPage() {
  const queryClient = useQueryClient()
  const hydrate = useThemeStore(s => s.hydrate)

  const { data: settings, isLoading } = useQuery({ queryKey: ['settings'], queryFn: getSettings })

  // On load, let the server's saved prefs win (cross-device sync).
  useEffect(() => {
    if (settings) {
      hydrate({
        theme: settings.preferences.theme as Theme,
        fontSize: settings.preferences.accessibility.font_size as FontSize,
        dyslexia: settings.preferences.accessibility.dyslexia_mode,
        reduceMotion: settings.preferences.accessibility.reduced_motion,
      })
    }
  }, [settings, hydrate])

  const saveMut = useMutation({
    mutationFn: (payload: UpdateSettingsPayload) => updateSettings(payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['settings'] }),
    onError: e => showToast(e instanceof Error ? e.message : 'Could not save', 'error'),
  })

  const savePrefs = (payload: UpdateSettingsPayload) => saveMut.mutate(payload)
  const saveAccount = (payload: UpdateSettingsPayload) =>
    saveMut.mutate(payload, {
      onSuccess: () => {
        queryClient.invalidateQueries({ queryKey: ['settings'] })
        showToast('Saved', 'success')
      },
    })

  const refetch = () => queryClient.invalidateQueries({ queryKey: ['settings'] })

  return (
    <div className="px-4 sm:px-6 py-6 max-w-5xl mx-auto w-full">
      <header className="mb-6">
        <p className="up-eyebrow text-secondary">Settings</p>
        <h1 className="text-2xl font-bold text-foreground mt-1">Your account</h1>
      </header>

      {isLoading || !settings ? (
        <div className="space-y-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="h-40 rounded-lg up-skeleton" />
          ))}
        </div>
      ) : (
        <div className="space-y-5">
          <AccountCard account={settings.account} onSave={saveAccount} saving={saveMut.isPending} />
          <SecurityCard
            mfaEnabled={settings.security.mfa_enabled}
            mfaMethod={settings.security.mfa_method}
            email={settings.account.email}
            pendingEmail={settings.account.pending_email}
            onChanged={refetch}
          />
          <PreferencesCard preferences={settings.preferences} onSave={savePrefs} saving={saveMut.isPending} />
          <NotificationsCard
            notifications={settings.notifications}
            emailEnabled={settings.email_enabled}
            emailFrequency={settings.email_frequency}
            onChanged={refetch}
          />
          <ConnectCard />
          <DataPrivacyCard />
          <BillingCard />
          <SignOutCard />
          <DangerZone deletion={settings.deletion} onChanged={refetch} />
        </div>
      )}
    </div>
  )
}
