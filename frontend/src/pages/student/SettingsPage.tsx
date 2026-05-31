import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { useAuthStore } from '../../stores/auth-store'
import { getNotificationPrefs, updateNotificationPrefs } from '../../api/notifications'
import Card from '../../components/ui/Card'
import Button from '../../components/ui/Button'
import BillingSection from '../../components/billing/BillingSection'
import { showToast } from '../../stores/toast-store'
import { useState, useEffect } from 'react'
import { formatDate } from '../../utils/format'
import { ShieldCheck, Bell, User, Database, LogOut, ChevronRight } from 'lucide-react'

const NOTIF_TYPES = [
  { key: 'application_updates', label: 'Application updates' },
  { key: 'new_matches', label: 'New matches' },
  { key: 'messages', label: 'Messages' },
  { key: 'events', label: 'Events & posts from saved programs' },
]

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
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notification-preferences'] })
      showToast('Preferences saved', 'success')
    },
  })

  return (
    <div className="p-6 max-w-2xl mx-auto space-y-6">
      <div>
        <p className="text-eyebrow uppercase tracking-[0.22em] text-cobalt font-semibold">Settings</p>
        <h1 className="text-2xl font-bold text-charcoal mt-1">Your account</h1>
      </div>

      {/* Account */}
      <Card className="p-5">
        <SectionHeader icon={User} title="Account" />
        <dl className="text-sm space-y-2">
          <Row label="Email" value={user?.email} />
          <Row label="Role" value={user?.role?.replace(/_/g, ' ')} capitalize />
          <Row label="Member since" value={formatDate(user?.created_at)} />
        </dl>
      </Card>

      {/* Plan & billing — Spec 07 (Product Context §4) */}
      <BillingSection />

      {/* Notifications */}
      <Card className="p-5">
        <SectionHeader icon={Bell} title="Notifications" />
        <div className="space-y-3">
          <label className="flex items-center gap-2 text-sm text-charcoal">
            <input type="checkbox" className="accent-cobalt" checked={emailEnabled} onChange={e => setEmailEnabled(e.target.checked)} />
            Email notifications enabled
          </label>
          {NOTIF_TYPES.map(t => (
            <label key={t.key} className="flex items-center gap-2 text-sm ml-6 text-charcoal">
              <input
                type="checkbox"
                className="accent-cobalt"
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

      {/* Data & privacy — single source of truth lives on the Profile Data tab */}
      <Card className="p-5">
        <SectionHeader icon={Database} title="Data & privacy" />
        <Link
          to="/s/profile?tab=data"
          className="flex items-center justify-between text-sm text-cobalt hover:underline"
        >
          <span className="flex items-center gap-2"><ShieldCheck size={15} /> Manage data rights, consent &amp; export</span>
          <ChevronRight size={16} />
        </Link>
      </Card>

      {/* Danger zone */}
      <Card className="p-5 border-error/40">
        <SectionHeader icon={LogOut} title="Danger zone" tone="danger" />
        <p className="text-sm text-slate mb-3">Sign out of this device, or contact support to permanently delete your account.</p>
        <div className="flex items-center gap-2">
          <Button variant="ghost" onClick={logout}>
            <LogOut size={14} className="mr-1.5" /> Sign out
          </Button>
          <a
            href="mailto:support@unipaith.co?subject=Delete%20my%20account"
            className="inline-flex items-center px-3 py-2 text-sm font-medium rounded-lg border border-error/40 text-error hover:bg-error-soft transition-colors"
          >
            Delete account
          </a>
        </div>
      </Card>
    </div>
  )
}

function SectionHeader({ icon: Icon, title, tone }: { icon: typeof User; title: string; tone?: 'danger' }) {
  return (
    <h2 className={`flex items-center gap-2 font-semibold mb-3 ${tone === 'danger' ? 'text-error' : 'text-charcoal'}`}>
      <Icon size={16} className={tone === 'danger' ? 'text-error' : 'text-cobalt'} />
      {title}
    </h2>
  )
}

function Row({ label, value, capitalize }: { label: string; value?: string | null; capitalize?: boolean }) {
  return (
    <div className="flex justify-between">
      <dt className="text-slate">{label}</dt>
      <dd className={`text-charcoal ${capitalize ? 'capitalize' : ''}`}>{value || '—'}</dd>
    </div>
  )
}
