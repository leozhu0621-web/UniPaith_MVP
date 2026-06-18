import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { UserPlus, Mail } from 'lucide-react'
import { getTeam, inviteTeamMember } from '../../../api/settings'
import Card from '../../../components/ui/Card'
import Button from '../../../components/ui/Button'
import Input from '../../../components/ui/Input'
import Select from '../../../components/ui/Select'
import Badge from '../../../components/ui/Badge'
import { showToast } from '../../../stores/toast-store'
import WizardFooter from './WizardFooter'

// Spec 30 §3.4 — roles: admissions / recruiter / marketing / IT.
const ROLES = [
  { value: 'admissions', label: 'Admissions' },
  { value: 'recruiter', label: 'Recruiter' },
  { value: 'marketing', label: 'Marketing' },
  { value: 'it', label: 'IT' },
]

export default function TeamStep({
  onFinish,
  onBack,
  finishing,
}: {
  onFinish: () => void
  onBack: () => void
  finishing: boolean
}) {
  const queryClient = useQueryClient()
  const [email, setEmail] = useState('')
  const [role, setRole] = useState('admissions')

  const teamQ = useQuery({ queryKey: ['institution-team'], queryFn: getTeam })
  const team = Array.isArray(teamQ.data) ? teamQ.data : []

  const invite = useMutation({
    mutationFn: () => inviteTeamMember(email.trim(), role),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['institution-team'] })
      queryClient.invalidateQueries({ queryKey: ['institution-setup'] })
      setEmail('')
      showToast('Invite added', 'success')
    },
    onError: (e: unknown) => {
      const msg = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      showToast(msg || 'Could not add invite', 'error')
    },
  })

  const emailValid = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim())

  return (
    <Card pad={false} className="p-5 sm:p-6">
      <h2 className="text-lg font-semibold text-foreground">Invite your team</h2>

      <div className="mt-5 flex flex-col gap-3 sm:flex-row sm:items-end">
        <div className="flex-1">
          <Input
            label="Email"
            type="email"
            placeholder="colleague@youruni.edu"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
        </div>
        <div className="sm:w-44">
          <Select label="Role" options={ROLES} value={role} onChange={(e) => setRole(e.target.value)} />
        </div>
        <Button
          variant="secondary"
          onClick={() => invite.mutate()}
          disabled={!emailValid}
          loading={invite.isPending}
          className="inline-flex items-center gap-2 sm:mb-[2px]"
        >
          <UserPlus size={15} /> Add
        </Button>
      </div>

      {team.length > 0 && (
        <ul className="mt-5 space-y-2">
          {team.map((m) => (
            <li
              key={m.id}
              className="flex items-center justify-between rounded-lg border border-border px-3 py-2"
            >
              <div className="flex items-center gap-2 min-w-0">
                <Mail size={15} className="shrink-0 text-muted-foreground" />
                <span className="truncate text-sm text-foreground">{m.email}</span>
                <span className="text-xs capitalize text-muted-foreground">· {m.role}</span>
              </div>
              <Badge variant={m.status === 'active' ? 'success' : 'neutral'}>{m.status}</Badge>
            </li>
          ))}
        </ul>
      )}

      {/* The single completion moment — the one earned gold accent (Spec 30 §8). */}
      <WizardFooter onBack={onBack}>
        <Button onClick={onFinish} loading={finishing}>
          Finish setup
        </Button>
      </WizardFooter>
    </Card>
  )
}
