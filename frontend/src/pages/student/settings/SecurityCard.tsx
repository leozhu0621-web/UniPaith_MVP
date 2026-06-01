import { useEffect, useRef, useState } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { ShieldCheck, KeyRound, Smartphone, Monitor, LogOut, Copy, Check, AlertTriangle } from 'lucide-react'
import clsx from 'clsx'
import Button from '../../../components/ui/Button'
import Input from '../../../components/ui/Input'
import Modal from '../../../components/ui/Modal'
import Badge from '../../../components/ui/Badge'
import SettingsSection from './SettingsSection'
import {
  changePassword,
  changeEmail,
  mfaEnroll,
  mfaConfirm,
  mfaDisable,
  getSessions,
  revokeSessions,
  getLoginActivity,
} from '../../../api/settings'
import { showToast } from '../../../stores/toast-store'
import { useAuthStore } from '../../../stores/auth-store'
import { formatDate } from '../../../utils/format'
import type { MfaEnrollResponse } from '../../../types'

type ModalKind = 'password' | 'email' | 'mfa-enroll' | 'mfa-disable' | null

interface SecurityCardProps {
  mfaEnabled: boolean
  mfaMethod: string | null
  email: string
  pendingEmail: string | null
  onChanged: () => void
}

export default function SecurityCard({
  mfaEnabled,
  mfaMethod,
  email,
  pendingEmail,
  onChanged,
}: SecurityCardProps) {
  const [modal, setModal] = useState<ModalKind>(null)
  const logout = useAuthStore(s => s.logout)

  const sessionsQ = useQuery({ queryKey: ['account-sessions'], queryFn: getSessions })
  const activityQ = useQuery({ queryKey: ['account-login-activity'], queryFn: getLoginActivity })

  const revokeMut = useMutation({
    mutationFn: revokeSessions,
    onSuccess: () => {
      showToast('Signed out of all other sessions', 'success')
      logout()
    },
    onError: () => showToast('Could not sign out everywhere', 'error'),
  })

  return (
    <SettingsSection
      icon={ShieldCheck}
      title="Security"
      description="Password, two-factor authentication, and active sessions."
    >
      <div className="divide-y divide-border">
        {/* Password */}
        <Row
          icon={KeyRound}
          title="Password"
          subtitle="Change the password you use to sign in."
          action={
            <Button variant="tertiary" size="sm" onClick={() => setModal('password')}>
              Change
            </Button>
          }
        />

        {/* Email */}
        <Row
          icon={ShieldCheck}
          title="Email address"
          subtitle={
            pendingEmail
              ? `Pending: ${pendingEmail} — check your new inbox to confirm.`
              : email
          }
          action={
            <Button variant="tertiary" size="sm" onClick={() => setModal('email')}>
              Change
            </Button>
          }
        />

        {/* MFA */}
        <Row
          icon={Smartphone}
          title="Two-factor authentication"
          subtitle={
            mfaEnabled
              ? `On · authenticator app${mfaMethod ? ` (${mfaMethod.toUpperCase()})` : ''}`
              : 'Add a second step at sign-in with an authenticator app.'
          }
          badge={mfaEnabled ? <Badge variant="success">Enabled</Badge> : undefined}
          action={
            mfaEnabled ? (
              <Button variant="ghost" size="sm" onClick={() => setModal('mfa-disable')}>
                Disable
              </Button>
            ) : (
              <Button variant="secondary" size="sm" onClick={() => setModal('mfa-enroll')}>
                Set up
              </Button>
            )
          }
        />
      </div>

      {/* Active sessions */}
      <div className="mt-4 pt-4 border-t border-border">
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-sm font-semibold text-foreground">Active sessions</h3>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => revokeMut.mutate()}
            loading={revokeMut.isPending}
          >
            <LogOut size={14} /> Sign out everywhere
          </Button>
        </div>
        <ul className="space-y-1.5">
          {(sessionsQ.data ?? []).map(s => (
            <li key={s.id} className="flex items-center gap-2 text-sm text-muted-foreground">
              <Monitor size={14} className="text-secondary" />
              <span className="text-foreground">{s.device}</span>
              {s.current && <Badge variant="info">This device</Badge>}
            </li>
          ))}
        </ul>
      </div>

      {/* Login activity */}
      <div className="mt-4 pt-4 border-t border-border">
        <h3 className="text-sm font-semibold text-foreground mb-2">Recent login activity</h3>
        {activityQ.data && activityQ.data.length > 0 ? (
          <ul className="space-y-1.5">
            {activityQ.data.map((e, i) => (
              <li key={i} className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">{e.device ?? 'Unknown device'}</span>
                <span className="text-muted-foreground tabular-nums">{formatDate(e.at)}</span>
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-sm text-muted-foreground">No recent activity recorded.</p>
        )}
      </div>

      {modal === 'password' && (
        <PasswordModal onClose={() => setModal(null)} onDone={() => setModal(null)} />
      )}
      {modal === 'email' && (
        <EmailModal
          onClose={() => setModal(null)}
          onDone={() => {
            setModal(null)
            onChanged()
          }}
        />
      )}
      {modal === 'mfa-enroll' && (
        <MfaEnrollModal
          onClose={() => setModal(null)}
          onDone={() => {
            setModal(null)
            onChanged()
          }}
        />
      )}
      {modal === 'mfa-disable' && (
        <MfaDisableModal
          onClose={() => setModal(null)}
          onDone={() => {
            setModal(null)
            onChanged()
          }}
        />
      )}
    </SettingsSection>
  )
}

function Row({
  icon: Icon,
  title,
  subtitle,
  action,
  badge,
}: {
  icon: typeof KeyRound
  title: string
  subtitle: string
  action: React.ReactNode
  badge?: React.ReactNode
}) {
  return (
    <div className="flex items-center justify-between gap-4 py-3">
      <div className="flex items-start gap-3 min-w-0">
        <Icon size={16} className="text-secondary mt-0.5 shrink-0" />
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium text-foreground">{title}</span>
            {badge}
          </div>
          <p className="text-xs text-muted-foreground mt-0.5 truncate">{subtitle}</p>
        </div>
      </div>
      <div className="shrink-0">{action}</div>
    </div>
  )
}

function passwordScore(pw: string): number {
  let score = 0
  if (pw.length >= 8) score++
  if (/[A-Za-z]/.test(pw) && /\d/.test(pw)) score++
  if (pw.length >= 12 || /[^A-Za-z0-9]/.test(pw)) score++
  return score
}

function PasswordModal({ onClose, onDone }: { onClose: () => void; onDone: () => void }) {
  const [current, setCurrent] = useState('')
  const [next, setNext] = useState('')
  const [confirm, setConfirm] = useState('')
  const mut = useMutation({
    mutationFn: () => changePassword(current, next),
    onSuccess: () => {
      showToast('Password changed', 'success')
      onDone()
    },
    onError: e => showToast(e instanceof Error ? e.message : 'Could not change password', 'error'),
  })
  const score = passwordScore(next)
  const mismatch = confirm.length > 0 && confirm !== next
  const canSubmit = current && next.length >= 8 && score >= 2 && !mismatch

  return (
    <Modal
      isOpen
      onClose={onClose}
      title="Change password"
      size="sm"
      footer={
        <>
          <Button variant="tertiary" onClick={onClose}>
            Cancel
          </Button>
          <Button variant="secondary" disabled={!canSubmit} loading={mut.isPending} onClick={() => mut.mutate()}>
            Update password
          </Button>
        </>
      }
    >
      <div className="space-y-3">
        <Input label="Current password" type="password" value={current} onChange={e => setCurrent(e.target.value)} />
        <div>
          <Input
            label="New password"
            type="password"
            value={next}
            onChange={e => setNext(e.target.value)}
            helperText="At least 8 characters, with letters and numbers."
          />
          <div className="flex gap-1 -mt-2" aria-hidden="true">
            {[0, 1, 2].map(i => (
              <span
                key={i}
                className={clsx(
                  'h-1 flex-1 rounded-full',
                  next.length === 0
                    ? 'bg-border'
                    : i < score
                      ? score >= 3
                        ? 'bg-success'
                        : 'bg-warning'
                      : 'bg-border'
                )}
              />
            ))}
          </div>
        </div>
        <Input
          label="Confirm new password"
          type="password"
          value={confirm}
          onChange={e => setConfirm(e.target.value)}
          error={mismatch ? 'Passwords do not match' : undefined}
        />
      </div>
    </Modal>
  )
}

function EmailModal({ onClose, onDone }: { onClose: () => void; onDone: () => void }) {
  const [value, setValue] = useState('')
  const mut = useMutation({
    mutationFn: () => changeEmail(value),
    onSuccess: () => {
      showToast('Check your new inbox to confirm your email.', 'success')
      onDone()
    },
    onError: e => showToast(e instanceof Error ? e.message : 'Could not change email', 'error'),
  })
  return (
    <Modal
      isOpen
      onClose={onClose}
      title="Change email"
      size="sm"
      footer={
        <>
          <Button variant="tertiary" onClick={onClose}>
            Cancel
          </Button>
          <Button variant="secondary" disabled={!value} loading={mut.isPending} onClick={() => mut.mutate()}>
            Send confirmation
          </Button>
        </>
      }
    >
      <Input
        label="New email address"
        type="email"
        value={value}
        onChange={e => setValue(e.target.value)}
        helperText="We'll email a confirmation link to the new address before switching."
      />
    </Modal>
  )
}

function MfaEnrollModal({ onClose, onDone }: { onClose: () => void; onDone: () => void }) {
  const [data, setData] = useState<MfaEnrollResponse | null>(null)
  const [code, setCode] = useState('')
  const [copied, setCopied] = useState(false)

  const enrollMut = useMutation({
    mutationFn: mfaEnroll,
    onSuccess: setData,
    onError: () => showToast('Could not start MFA setup', 'error'),
  })
  const confirmMut = useMutation({
    mutationFn: () => mfaConfirm(code),
    onSuccess: () => {
      showToast('Two-factor authentication enabled', 'success')
      onDone()
    },
    onError: e => showToast(e instanceof Error ? e.message : 'That code is incorrect', 'error'),
  })

  // Kick off enrollment once on open (ref guard survives StrictMode double-mount).
  const started = useRef(false)
  useEffect(() => {
    if (!started.current) {
      started.current = true
      enrollMut.mutate()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const copyKey = () => {
    if (data) {
      navigator.clipboard?.writeText(data.secret)
      setCopied(true)
      setTimeout(() => setCopied(false), 1500)
    }
  }

  return (
    <Modal
      isOpen
      onClose={onClose}
      title="Set up two-factor authentication"
      size="sm"
      footer={
        <>
          <Button variant="tertiary" onClick={onClose}>
            Cancel
          </Button>
          <Button
            variant="secondary"
            disabled={!data || code.length < 6}
            loading={confirmMut.isPending}
            onClick={() => confirmMut.mutate()}
          >
            Verify & enable
          </Button>
        </>
      }
    >
      {!data ? (
        <p className="text-sm text-muted-foreground">Preparing your setup key…</p>
      ) : (
        <div className="space-y-4">
          <ol className="text-sm text-muted-foreground list-decimal pl-5 space-y-1">
            <li>Open your authenticator app (Google Authenticator, Authy, 1Password…).</li>
            <li>Scan the QR code or enter the setup key manually.</li>
            <li>Enter the 6-digit code it shows below.</li>
          </ol>
          <div className="flex flex-col items-center gap-3 sm:flex-row sm:items-start">
            <img
              src={`https://api.qrserver.com/v1/create-qr-code/?size=160x160&data=${encodeURIComponent(data.otpauth_uri)}`}
              alt="Scan with your authenticator app"
              width={160}
              height={160}
              className="rounded-lg border border-border bg-card p-2 shrink-0"
            />
            <p className="text-xs text-muted-foreground sm:pt-2">
              Can't scan? Copy the setup key below and paste it into your app.
            </p>
          </div>
          <div className="flex items-center gap-2 rounded-lg border border-border bg-muted px-3 py-2">
            <code className="text-sm font-mono text-foreground break-all flex-1">{data.secret}</code>
            <button
              type="button"
              onClick={copyKey}
              aria-label="Copy setup key"
              className="ui-btn p-1.5 rounded-md text-muted-foreground hover:bg-card hover:text-foreground"
            >
              {copied ? <Check size={15} className="text-success" /> : <Copy size={15} />}
            </button>
          </div>

          <Input
            label="6-digit code"
            inputMode="numeric"
            maxLength={6}
            value={code}
            onChange={e => setCode(e.target.value.replace(/\D/g, ''))}
            placeholder="123456"
          />

          <div className="rounded-lg border border-border bg-card p-3">
            <p className="text-xs font-semibold text-foreground mb-1.5">Recovery codes</p>
            <p className="text-xs text-muted-foreground mb-2">
              Save these somewhere safe — each can be used once if you lose your device.
            </p>
            <div className="grid grid-cols-2 gap-1.5">
              {data.recovery_codes.map(c => (
                <code key={c} className="text-xs font-mono text-foreground bg-muted rounded px-2 py-1 text-center">
                  {c}
                </code>
              ))}
            </div>
          </div>
        </div>
      )}
    </Modal>
  )
}

function MfaDisableModal({ onClose, onDone }: { onClose: () => void; onDone: () => void }) {
  const [code, setCode] = useState('')
  const mut = useMutation({
    mutationFn: () => mfaDisable(code),
    onSuccess: () => {
      showToast('Two-factor authentication disabled', 'success')
      onDone()
    },
    onError: e => showToast(e instanceof Error ? e.message : 'That code is incorrect', 'error'),
  })
  return (
    <Modal
      isOpen
      onClose={onClose}
      title="Disable two-factor authentication"
      size="sm"
      footer={
        <>
          <Button variant="tertiary" onClick={onClose}>
            Cancel
          </Button>
          <Button variant="destructive" disabled={code.length < 6} loading={mut.isPending} onClick={() => mut.mutate()}>
            Disable 2FA
          </Button>
        </>
      }
    >
      <div className="space-y-3">
        <div className="flex items-start gap-2 rounded-lg border border-warning/40 bg-warning-soft/40 p-3 text-sm text-foreground">
          <AlertTriangle size={16} className="text-warning mt-0.5 shrink-0" />
          Disabling 2FA makes your account less secure. Enter a current code or a recovery code to confirm.
        </div>
        <Input
          label="Authenticator or recovery code"
          value={code}
          onChange={e => setCode(e.target.value.trim())}
          placeholder="123456"
        />
      </div>
    </Modal>
  )
}
