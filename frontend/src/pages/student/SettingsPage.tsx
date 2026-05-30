import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useAuthStore } from '../../stores/auth-store'
import { getNotificationPrefs, updateNotificationPrefs } from '../../api/notifications'
import {
  getAccount,
  updateAccount,
  requestAccountDeletion,
  cancelAccountDeletion,
  changePassword,
} from '../../api/account'
import Card from '../../components/ui/Card'
import Button from '../../components/ui/Button'
import Input from '../../components/ui/Input'
import Select from '../../components/ui/Select'
import { showToast } from '../../stores/toast-store'
import { formatDate } from '../../utils/format'
import { Globe, Lock, ShieldCheck, Trash2, AlertTriangle, Bell, LogOut } from 'lucide-react'

const LOCALE_OPTIONS = [
  { value: '', label: 'System default' },
  { value: 'en', label: 'English' },
  { value: 'en-US', label: 'English (US)' },
  { value: 'en-GB', label: 'English (UK)' },
  { value: 'zh', label: '中文 (Chinese)' },
  { value: 'es', label: 'Español (Spanish)' },
  { value: 'fr', label: 'Français (French)' },
  { value: 'de', label: 'Deutsch (German)' },
  { value: 'hi', label: 'हिन्दी (Hindi)' },
  { value: 'ja', label: '日本語 (Japanese)' },
  { value: 'ko', label: '한국어 (Korean)' },
]

const TIMEZONE_OPTIONS = [
  { value: '', label: 'System default' },
  { value: 'America/New_York', label: 'New York (ET)' },
  { value: 'America/Chicago', label: 'Chicago (CT)' },
  { value: 'America/Denver', label: 'Denver (MT)' },
  { value: 'America/Los_Angeles', label: 'Los Angeles (PT)' },
  { value: 'Europe/London', label: 'London' },
  { value: 'Europe/Paris', label: 'Paris' },
  { value: 'Asia/Shanghai', label: 'Shanghai' },
  { value: 'Asia/Tokyo', label: 'Tokyo' },
  { value: 'Asia/Kolkata', label: 'Kolkata' },
  { value: 'Australia/Sydney', label: 'Sydney' },
]

export default function SettingsPage() {
  const { user, logout } = useAuthStore()
  const queryClient = useQueryClient()

  const [locale, setLocale] = useState('')
  const [timezone, setTimezone] = useState('')
  const [emailEnabled, setEmailEnabled] = useState(true)
  const [prefs, setPrefs] = useState<Record<string, boolean>>({})

  // Password change state.
  const [currentPw, setCurrentPw] = useState('')
  const [newPw, setNewPw] = useState('')
  const [confirmPw, setConfirmPw] = useState('')

  // Deletion confirmation modal-by-checkbox.
  const [deleteAcknowledged, setDeleteAcknowledged] = useState(false)

  const accountQ = useQuery({ queryKey: ['account'], queryFn: getAccount })
  const notifQ = useQuery({ queryKey: ['notification-preferences'], queryFn: getNotificationPrefs })

  useEffect(() => {
    if (accountQ.data) {
      setLocale(accountQ.data.locale ?? '')
      setTimezone(accountQ.data.timezone ?? '')
    }
  }, [accountQ.data])
  useEffect(() => {
    if (notifQ.data) {
      setEmailEnabled(notifQ.data.email_enabled)
      setPrefs(notifQ.data.preferences || {})
    }
  }, [notifQ.data])

  const accountMut = useMutation({
    mutationFn: () => updateAccount({ locale: locale || null, timezone: timezone || null }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['account'] })
      showToast('Preferences saved', 'success')
    },
  })
  const notifMut = useMutation({
    mutationFn: () => updateNotificationPrefs({ email_enabled: emailEnabled, preferences: prefs }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notification-preferences'] })
      showToast('Notification preferences saved', 'success')
    },
  })
  const passwordMut = useMutation({
    mutationFn: () => changePassword(currentPw, newPw),
    onSuccess: () => {
      setCurrentPw('')
      setNewPw('')
      setConfirmPw('')
      showToast('Password updated', 'success')
    },
    onError: () => showToast('Could not change password — try again', 'error'),
  })
  const deleteMut = useMutation({
    mutationFn: requestAccountDeletion,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['account'] })
      showToast('Account deletion requested. You have 30 days to cancel.', 'success')
    },
  })
  const cancelDeleteMut = useMutation({
    mutationFn: cancelAccountDeletion,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['account'] })
      showToast('Deletion cancelled', 'success')
    },
  })

  const account = accountQ.data
  const deletionPending = !!account?.deletion_requested_at

  const notifTypes = [
    { key: 'application_updates', label: 'Application updates' },
    { key: 'new_matches', label: 'New matches' },
    { key: 'messages', label: 'Messages' },
    { key: 'events', label: 'Marketing & events' },
  ]

  const passwordsMatch = newPw === confirmPw
  const passwordValid = newPw.length >= 8 && passwordsMatch && currentPw.length > 0

  return (
    <div className="p-6 max-w-2xl mx-auto space-y-6">
      <header>
        <p className="up-eyebrow">Settings</p>
        <h1 className="text-h1 mt-1">Your account</h1>
      </header>

      {/* Account ------------------------------------------------- */}
      <Card className="p-5">
        <h2 className="text-h3 mb-3">Account</h2>
        <dl className="text-sm space-y-2">
          <div className="flex justify-between"><dt className="text-slate">Email</dt><dd className="text-charcoal font-bold">{user?.email}</dd></div>
          <div className="flex justify-between"><dt className="text-slate">Role</dt><dd className="text-charcoal capitalize">{user?.role?.replace(/_/g, ' ')}</dd></div>
          <div className="flex justify-between"><dt className="text-slate">Member since</dt><dd className="text-charcoal">{formatDate(user?.created_at)}</dd></div>
        </dl>
      </Card>

      {/* Locale + timezone --------------------------------------- */}
      <Card className="p-5">
        <div className="flex items-center gap-2 mb-3">
          <Globe size={16} className="text-cobalt" />
          <h2 className="text-h3">Locale &amp; timezone</h2>
        </div>
        <div className="grid sm:grid-cols-2 gap-3 mb-4">
          <Select
            label="Language"
            value={locale}
            onChange={e => setLocale(e.target.value)}
            options={LOCALE_OPTIONS}
          />
          <Select
            label="Timezone"
            value={timezone}
            onChange={e => setTimezone(e.target.value)}
            options={TIMEZONE_OPTIONS}
          />
        </div>
        <Button size="sm" onClick={() => accountMut.mutate()} loading={accountMut.isPending}>
          Save preferences
        </Button>
      </Card>

      {/* Notifications ------------------------------------------- */}
      <Card className="p-5">
        <div className="flex items-center gap-2 mb-3">
          <Bell size={16} className="text-cobalt" />
          <h2 className="text-h3">Notifications</h2>
        </div>
        <div className="space-y-3">
          <label className="flex items-center gap-2 text-sm text-charcoal">
            <input type="checkbox" checked={emailEnabled} onChange={e => setEmailEnabled(e.target.checked)} />
            Email notifications enabled
          </label>
          {notifTypes.map(t => (
            <label key={t.key} className="flex items-center gap-2 text-sm ml-4 text-charcoal">
              <input
                type="checkbox"
                checked={prefs[t.key] ?? true}
                onChange={e => setPrefs(p => ({ ...p, [t.key]: e.target.checked }))}
                disabled={!emailEnabled}
              />
              {t.label}
            </label>
          ))}
          <Button size="sm" onClick={() => notifMut.mutate()} loading={notifMut.isPending}>
            Save preferences
          </Button>
        </div>
      </Card>

      {/* Password ------------------------------------------------ */}
      <Card className="p-5">
        <div className="flex items-center gap-2 mb-3">
          <Lock size={16} className="text-cobalt" />
          <h2 className="text-h3">Change password</h2>
        </div>
        <div className="space-y-3">
          <Input
            type="password"
            label="Current password"
            value={currentPw}
            onChange={e => setCurrentPw(e.target.value)}
          />
          <Input
            type="password"
            label="New password"
            value={newPw}
            onChange={e => setNewPw(e.target.value)}
            error={newPw && newPw.length < 8 ? 'At least 8 characters' : undefined}
          />
          <Input
            type="password"
            label="Confirm new password"
            value={confirmPw}
            onChange={e => setConfirmPw(e.target.value)}
            error={confirmPw && !passwordsMatch ? "Doesn't match" : undefined}
          />
          <Button
            size="sm"
            disabled={!passwordValid}
            onClick={() => passwordMut.mutate()}
            loading={passwordMut.isPending}
          >
            Update password
          </Button>
        </div>
      </Card>

      {/* Two-factor ---------------------------------------------- */}
      <Card className="p-5">
        <div className="flex items-center gap-2 mb-3">
          <ShieldCheck size={16} className="text-cobalt" />
          <h2 className="text-h3">Two-factor authentication</h2>
        </div>
        <p className="text-sm text-slate">
          TOTP-based 2FA via Cognito is in the next release. Until then, use a strong
          password and keep your recovery email up to date.
        </p>
      </Card>

      {/* Account deletion ---------------------------------------- */}
      <Card className="p-5 border-error/40">
        <div className="flex items-center gap-2 mb-3">
          <AlertTriangle size={16} className="text-error" />
          <h2 className="text-h3 text-error">Delete account</h2>
        </div>
        {deletionPending ? (
          <div className="space-y-3">
            <p className="text-sm text-charcoal">
              Your account is scheduled for deletion on{' '}
              <strong>
                {account?.deletion_requested_at &&
                  new Date(
                    new Date(account.deletion_requested_at).getTime() + 30 * 86400 * 1000,
                  ).toLocaleDateString()}
              </strong>
              . You can cancel at any time during the 30-day grace period.
            </p>
            <Button
              variant="secondary"
              onClick={() => cancelDeleteMut.mutate()}
              loading={cancelDeleteMut.isPending}
            >
              Cancel deletion request
            </Button>
          </div>
        ) : (
          <div className="space-y-3">
            <p className="text-sm text-slate">
              This permanently removes your profile, applications, messages, and saved
              programs after a 30-day grace period. The action is reversible during the
              grace window.
            </p>
            <label className="flex items-start gap-2 text-sm text-charcoal">
              <input
                type="checkbox"
                className="mt-1"
                checked={deleteAcknowledged}
                onChange={e => setDeleteAcknowledged(e.target.checked)}
              />
              <span>
                I understand my data will be deleted after the 30-day grace period.
              </span>
            </label>
            <Button
              variant="danger"
              disabled={!deleteAcknowledged}
              onClick={() => deleteMut.mutate()}
              loading={deleteMut.isPending}
            >
              <Trash2 size={14} className="mr-1" /> Request account deletion
            </Button>
          </div>
        )}
      </Card>

      {/* Sign out ------------------------------------------------ */}
      <div className="flex justify-end">
        <Button variant="ghost" onClick={logout}>
          <LogOut size={14} className="mr-1" /> Sign out
        </Button>
      </div>
    </div>
  )
}
