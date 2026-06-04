import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Users, UserPlus, Trash2, Mail } from 'lucide-react'
import Button from '../../../components/ui/Button'
import Input from '../../../components/ui/Input'
import Select from '../../../components/ui/Select'
import Badge from '../../../components/ui/Badge'
import SettingsSection from '../../student/settings/SettingsSection'
import QueryError from '../../../components/ui/QueryError'
import { getTeam, inviteTeamMember, revokeTeamInvite } from '../../../api/settings'
import { showToast } from '../../../stores/toast-store'
import { confirmDialog } from '../../../stores/confirm-store'

const ROLES = [
  { value: 'admissions', label: 'Admissions' },
  { value: 'recruiter', label: 'Recruiter' },
  { value: 'marketing', label: 'Marketing' },
  { value: 'it', label: 'IT' },
  { value: 'admin', label: 'Admin' },
]

export default function TeamCard() {
  const queryClient = useQueryClient()
  const [email, setEmail] = useState('')
  const [role, setRole] = useState('admissions')

  const teamQ = useQuery({ queryKey: ['institution-team'], queryFn: getTeam })

  const inviteMut = useMutation({
    mutationFn: () => inviteTeamMember(email, role),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['institution-team'] })
      showToast('Invite created', 'success')
      setEmail('')
    },
    onError: e => showToast(e instanceof Error ? e.message : 'Could not invite', 'error'),
  })

  const revokeMut = useMutation({
    mutationFn: (id: string) => revokeTeamInvite(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['institution-team'] })
      showToast('Invite revoked', 'success')
    },
    onError: () => showToast('Could not revoke invite', 'error'),
  })

  const revoke = async (id: string, memberEmail: string) => {
    const ok = await confirmDialog({
      title: 'Revoke invite?',
      body: `${memberEmail} will no longer be able to join your team with this invitation.`,
      confirmLabel: 'Revoke invite',
      destructive: true,
    })
    if (ok) revokeMut.mutate(id)
  }

  const members = teamQ.data ?? []

  return (
    <SettingsSection
      icon={Users}
      title="Team & seats"
      description="Invite staff and assign roles. Invitations send when email integration goes live (Phase 2)."
    >
      {/* Invite row */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-end mb-4">
        <div className="flex-1">
          <Input
            label="Invite by email"
            type="email"
            value={email}
            onChange={e => setEmail(e.target.value)}
            placeholder="colleague@school.edu"
            leftIcon={<Mail size={15} />}
          />
        </div>
        <div className="w-full sm:w-44">
          <Select label="Role" options={ROLES} value={role} onChange={e => setRole(e.target.value)} />
        </div>
        <div className="pb-[26px]">
          <Button
            variant="secondary"
            disabled={!email || inviteMut.isPending}
            loading={inviteMut.isPending}
            onClick={() => inviteMut.mutate()}
          >
            <UserPlus size={15} /> Invite
          </Button>
        </div>
      </div>

      {/* Member list */}
      {teamQ.isError ? (
        <QueryError
          variant="inline"
          detail="We couldn't load your team."
          onRetry={() => teamQ.refetch()}
        />
      ) : (
      <ul className="divide-y divide-border border-t border-border">
        {members.map(m => (
          <li key={m.id} className="flex items-center justify-between gap-3 py-3">
            <div className="min-w-0">
              <p className="text-sm font-medium text-foreground truncate">{m.email}</p>
              <p className="text-xs text-muted-foreground capitalize">{m.role}</p>
            </div>
            <div className="flex items-center gap-2 shrink-0">
              <Badge variant={m.status === 'active' ? 'success' : 'warning'}>
                {m.status === 'active' ? 'Active' : 'Pending'}
              </Badge>
              {m.status === 'pending' && (
                <button
                  onClick={() => revoke(m.id, m.email)}
                  disabled={revokeMut.isPending}
                  aria-label={`Revoke invite for ${m.email}`}
                  className="ui-btn p-1.5 rounded-md text-muted-foreground hover:bg-error-soft hover:text-error transition-colors"
                >
                  <Trash2 size={15} />
                </button>
              )}
            </div>
          </li>
        ))}
      </ul>
      )}
    </SettingsSection>
  )
}
