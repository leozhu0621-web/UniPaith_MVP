import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { useAuthStore } from '../../stores/auth-store'
import { getNotificationPrefs, updateNotificationPrefs } from '../../api/notifications'
import {
  cancelStudentBilling,
  resumeStudentBilling,
  setAdFree,
  upgradeStudentBilling,
  type StudentBilling,
} from '../../api/billing'
import { useStudentBilling } from '../../hooks/useBilling'
import Card from '../../components/ui/Card'
import Button from '../../components/ui/Button'
import Badge from '../../components/ui/Badge'
import { showToast } from '../../stores/toast-store'
import { useState, useEffect } from 'react'
import { formatDate } from '../../utils/format'
import { ShieldCheck, Bell, User, Database, LogOut, ChevronRight, CreditCard, Sparkles, Check, Users } from 'lucide-react'
import { getPreferences, upsertPreferences } from '../../api/students'

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

      {/* Billing — Spec 07 §4.1 / 21 §2.7 */}
      <BillingSection />

      {/* Connect — Spec 20 §2 */}
      <ConnectPreferencesSection />

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

function ConnectPreferencesSection() {
  const queryClient = useQueryClient()
  const { data: prefs, isLoading } = useQuery({
    queryKey: ['student-preferences'],
    queryFn: getPreferences,
    retry: false,
  })

  const saveMut = useMutation({
    mutationFn: (autoFollow: boolean) => upsertPreferences({ auto_follow_on_save: autoFollow }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['student-preferences'] })
      queryClient.invalidateQueries({ queryKey: ['connect-follows'] })
      queryClient.invalidateQueries({ queryKey: ['connect-feed'] })
      showToast('Connect preferences saved', 'success')
    },
    onError: () => showToast("Something didn't work. Try again.", 'error'),
  })

  const autoFollow = prefs?.auto_follow_on_save ?? true

  return (
    <Card className="p-5">
      <SectionHeader icon={Users} title="Connect" />
      {isLoading ? (
        <div className="h-12 animate-pulse rounded-lg bg-muted" />
      ) : (
        <div className="flex items-start justify-between gap-4">
          <div>
            <p className="text-sm font-medium text-charcoal">Auto-follow when I save a program</p>
            <p className="text-xs text-slate mt-0.5 max-w-md">
              When on, saving a program follows its institution so updates and events appear in Connect.
              Starting an application always follows — that cannot be disabled while you are applying.
            </p>
          </div>
          <Toggle
            checked={autoFollow}
            disabled={saveMut.isPending}
            onChange={v => saveMut.mutate(v)}
            label="Auto-follow on save"
          />
        </div>
      )}
    </Card>
  )
}

function BillingSection() {
  const queryClient = useQueryClient()
  const { data: billing, isLoading } = useStudentBilling()

  const refresh = (next: StudentBilling) => {
    queryClient.setQueryData(['student-billing'], next)
    queryClient.invalidateQueries({ queryKey: ['student-billing'] })
  }

  const upgradeMut = useMutation({
    mutationFn: upgradeStudentBilling,
    onSuccess: d => { refresh(d); showToast('You’re on UniPaith Plus', 'success') },
    onError: () => showToast('Could not update your plan', 'error'),
  })
  const adFreeMut = useMutation({
    mutationFn: (enabled: boolean) => setAdFree(enabled),
    onSuccess: refresh,
    onError: () => showToast('Could not update ad-free', 'error'),
  })
  const cancelMut = useMutation({
    mutationFn: cancelStudentBilling,
    onSuccess: d => { refresh(d); showToast('Plan will cancel at period end', 'success') },
    onError: () => showToast('Could not cancel', 'error'),
  })
  const resumeMut = useMutation({
    mutationFn: resumeStudentBilling,
    onSuccess: d => { refresh(d); showToast('Plan resumed', 'success') },
    onError: () => showToast('Could not resume', 'error'),
  })

  const busy = upgradeMut.isPending || cancelMut.isPending || resumeMut.isPending

  return (
    <Card className="p-5">
      <SectionHeader icon={CreditCard} title="Billing & plan" />
      {isLoading || !billing ? (
        <div className="h-16 animate-pulse rounded-lg bg-muted" />
      ) : (
        <div className="space-y-4">
          {/* Plan status row */}
          <div className="flex items-start justify-between gap-3">
            <div>
              <div className="flex items-center gap-2">
                <span className="font-semibold text-charcoal">UniPaith Plus</span>
                <PlanBadge billing={billing} />
              </div>
              <p className="text-sm text-slate mt-0.5">{planDescription(billing)}</p>
            </div>
            <div className="text-right shrink-0">
              <div className="text-lg font-bold text-charcoal">${billing.monthly_total_usd}<span className="text-xs font-normal text-slate">/mo</span></div>
              {billing.ad_free && <div className="text-xs text-slate">incl. ad-free</div>}
            </div>
          </div>

          {/* Card on file */}
          {billing.has_payment_method && (
            <div className="flex items-center gap-2 text-sm text-slate">
              <CreditCard size={14} className="text-cobalt" />
              {billing.payment_method_brand} •••• {billing.payment_method_last4}
            </div>
          )}

          {/* Ad-free upgrade toggle (Spec 07 §4.1 — +$5/mo) */}
          <div className="flex items-center justify-between rounded-lg border border-stone/60 bg-student-moss/40 px-3 py-2.5">
            <div>
              <p className="text-sm font-medium text-charcoal flex items-center gap-1.5">
                <Sparkles size={14} className="text-cobalt" /> Ad-free experience
              </p>
              <p className="text-xs text-slate">Remove ads across UniPaith · +${billing.ad_free_addon_usd}/mo</p>
            </div>
            <Toggle
              checked={billing.ad_free}
              disabled={adFreeMut.isPending}
              onChange={v => adFreeMut.mutate(v)}
              label="Ad-free"
            />
          </div>

          {/* Upcoming invoice */}
          {billing.invoices.length > 0 && (
            <div className="text-sm text-slate">
              Next charge: <span className="text-charcoal font-medium">${billing.invoices[0].amount_usd}</span> on {formatDate(billing.invoices[0].date)}
            </div>
          )}

          {/* Actions */}
          <div className="flex flex-wrap items-center gap-2 pt-1">
            {(billing.status === 'trialing' || billing.status === 'expired') && (
              <Button size="sm" onClick={() => upgradeMut.mutate()} loading={upgradeMut.isPending}>
                {billing.status === 'expired' ? 'Reactivate — $15/mo' : 'Upgrade to Plus — $15/mo'}
              </Button>
            )}
            {billing.status === 'active' && (
              <Button size="sm" variant="ghost" onClick={() => cancelMut.mutate()} loading={cancelMut.isPending} disabled={busy}>
                Cancel plan
              </Button>
            )}
            {billing.status === 'canceled' && (
              <Button size="sm" onClick={() => resumeMut.mutate()} loading={resumeMut.isPending} disabled={busy}>
                Resume plan
              </Button>
            )}
          </div>
        </div>
      )}
    </Card>
  )
}

function PlanBadge({ billing }: { billing: StudentBilling }) {
  if (billing.status === 'trialing') {
    return <Badge variant="info">Free trial · {billing.trial_days_left}d left</Badge>
  }
  if (billing.status === 'active') return <Badge variant="success">Active</Badge>
  if (billing.status === 'canceled') return <Badge variant="warning">Ends soon</Badge>
  return <Badge variant="neutral">Trial ended</Badge>
}

function planDescription(billing: StudentBilling): string {
  switch (billing.status) {
    case 'trialing':
      return `Your free trial ends ${formatDate(billing.trial_ends_at)}. Add a card to keep full access.`
    case 'active':
      return `Renews ${formatDate(billing.current_period_end)}.`
    case 'canceled':
      return `Access continues until ${formatDate(billing.current_period_end)}, then your plan ends.`
    default:
      return 'Your trial has ended. Reactivate to regain full access.'
  }
}

function Toggle({ checked, onChange, disabled, label }: { checked: boolean; onChange: (v: boolean) => void; disabled?: boolean; label: string }) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      aria-label={label}
      disabled={disabled}
      onClick={() => onChange(!checked)}
      className={`relative inline-flex h-6 w-11 shrink-0 items-center rounded-pill transition-colors disabled:opacity-50 ${checked ? 'bg-cobalt' : 'bg-stone'}`}
    >
      <span className={`inline-flex h-5 w-5 items-center justify-center rounded-full bg-white shadow transition-transform ${checked ? 'translate-x-5' : 'translate-x-0.5'}`}>
        {checked && <Check size={12} className="text-cobalt" />}
      </span>
    </button>
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
