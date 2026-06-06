import { useEffect, useState } from 'react'
import { User } from 'lucide-react'
import Input from '../../../components/ui/Input'
import Button from '../../../components/ui/Button'
import Avatar from '../../../components/ui/Avatar'
import SettingsSection from './SettingsSection'
import { formatDate } from '../../../utils/format'
import type { UserSettings } from '../../../types'
import type { UpdateSettingsPayload } from '../../../api/settings'

interface AccountCardProps {
  account: UserSettings['account']
  onSave: (payload: UpdateSettingsPayload) => void
  saving?: boolean
}

export default function AccountCard({ account, onSave, saving }: AccountCardProps) {
  const [displayName, setDisplayName] = useState(account.display_name ?? '')
  const [photoUrl, setPhotoUrl] = useState(account.photo_url ?? '')

  useEffect(() => {
    setDisplayName(account.display_name ?? '')
    setPhotoUrl(account.photo_url ?? '')
  }, [account.display_name, account.photo_url])

  const dirty = displayName !== (account.display_name ?? '') || photoUrl !== (account.photo_url ?? '')

  return (
    <SettingsSection icon={User} title="Account" description="Your identity on UniPaith.">
      {/* Read-only identity */}
      <dl className="grid gap-x-6 gap-y-2 sm:grid-cols-2 text-sm mb-5">
        <div className="flex justify-between sm:block">
          <dt className="text-muted-foreground sm:text-xs sm:uppercase sm:tracking-wide sm:font-semibold">
            Email
          </dt>
          <dd className="text-foreground sm:mt-0.5 flex items-center gap-2">
            <span>{account.email || '—'}</span>
            <a
              href="#security"
              onClick={e => {
                e.preventDefault()
                document.getElementById('settings-security-section')?.scrollIntoView({ behavior: 'smooth' })
              }}
              className="text-xs font-medium text-secondary hover:underline"
            >
              Change
            </a>
          </dd>
        </div>
        <Field label="Role" value={account.role.replace(/_/g, ' ')} capitalize />
        <Field label="Member since" value={formatDate(account.member_since)} />
      </dl>

      {/* Editable display name + photo */}
      <div className="flex items-start gap-4 border-t border-border pt-4">
        {photoUrl ? (
          <img
            src={photoUrl}
            alt=""
            className="h-12 w-12 rounded-full object-cover border border-border shrink-0"
            onError={e => ((e.target as HTMLImageElement).style.display = 'none')}
          />
        ) : (
          <Avatar name={displayName || account.email} size="lg" />
        )}
        <div className="flex-1 grid gap-3 sm:grid-cols-2">
          <Input
            label="Display name"
            value={displayName}
            onChange={e => setDisplayName(e.target.value)}
            placeholder="How your name appears"
          />
          <Input
            label="Profile photo URL"
            value={photoUrl}
            onChange={e => setPhotoUrl(e.target.value)}
            placeholder="https://…"
          />
        </div>
      </div>
      <div className="flex justify-end mt-1">
        <Button
          variant="secondary"
          size="sm"
          disabled={!dirty || saving}
          loading={saving}
          onClick={() => onSave({ display_name: displayName, photo_url: photoUrl })}
        >
          Save
        </Button>
      </div>
    </SettingsSection>
  )
}

function Field({ label, value, capitalize }: { label: string; value?: string | null; capitalize?: boolean }) {
  return (
    <div className="flex justify-between sm:block">
      <dt className="text-muted-foreground sm:text-xs sm:uppercase sm:tracking-wide sm:font-semibold">
        {label}
      </dt>
      <dd className={`text-foreground sm:mt-0.5 ${capitalize ? 'capitalize' : ''}`}>{value || '—'}</dd>
    </div>
  )
}
