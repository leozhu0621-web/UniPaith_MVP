/**
 * Profile → Personal tab (key `overview`).
 *
 * The lean personal header — avatar, name, headline, location, bio, and the
 * "Edit personal info" form (the single place to edit your basic record). The
 * old completion-map + "what's next" Summary view was retired (2026-06-15) —
 * the My Space rail already lists every profile section, and the home
 * (/s/space) carries the next-actions queue, so both were redundant here.
 */
import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Pencil } from 'lucide-react'

import Button from '../../../components/ui/Button'
import Card from '../../../components/ui/Card'
import Modal from '../../../components/ui/Modal'
import { SkeletonCard } from '../../../components/ui/Skeleton'
import { getProfile, updateProfile } from '../../../api/students'
import { useAuthStore } from '../../../stores/auth-store'
import { showToast } from '../../../stores/toast-store'
import { initials } from '../../../utils/format'
import { DEGREE_LABELS } from '../../../utils/constants'
import { BasicInfoForm } from '../components/ProfileForms'

export default function OverviewTab() {
  const qc = useQueryClient()
  const { user } = useAuthStore()
  const { data: profile, isLoading } = useQuery({ queryKey: ['profile'], queryFn: getProfile })
  const [editOpen, setEditOpen] = useState(false)

  const profileMut = useMutation({
    mutationFn: (data: any) => updateProfile(data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['profile'] })
      qc.invalidateQueries({ queryKey: ['onboarding'] })
      setEditOpen(false)
      showToast('Saved', 'success')
    },
    onError: () => showToast("Something didn't work. Try again.", 'error'),
  })

  if (isLoading || !profile) return <SkeletonCard />

  const p: any = profile
  const fullName = [p.first_name, p.last_name].filter(Boolean).join(' ') || 'Your name'
  const latestAcademic = (p.academic_records ?? [])[0]
  const headline = latestAcademic
    ? [
        DEGREE_LABELS[latestAcademic.degree_type] || latestAcademic.degree_type,
        latestAcademic.field_of_study,
        latestAcademic.institution_name,
      ].filter(Boolean).join(' · ')
    : null
  const locationLine = [p.country_of_residence, p.nationality, p.preferred_pronouns ? `(${p.preferred_pronouns})` : null].filter(Boolean).join(' · ')

  return (
    <div className="space-y-6">
      <Card pad={false} className="p-6">
        <div className="flex items-start gap-5">
          <div className="h-20 w-20 shrink-0 rounded-full bg-muted text-foreground flex items-center justify-center text-2xl font-bold">
            {initials(fullName)}
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
              <h2 className="text-h2 text-foreground truncate">{fullName}</h2>
              {user?.email && <span className="text-sm text-muted-foreground truncate">{user.email}</span>}
            </div>
            {headline && <p className="text-sm text-foreground mt-1">{headline}</p>}
            {locationLine && <p className="text-sm text-muted-foreground mt-0.5">{locationLine}</p>}
            {p.bio_text && <p className="text-sm text-muted-foreground mt-2 max-w-prose">{p.bio_text}</p>}
            <Button variant="tertiary" size="sm" className="mt-3" onClick={() => setEditOpen(true)}>
              <Pencil size={14} /> Edit personal info
            </Button>
          </div>
        </div>
      </Card>

      <Modal isOpen={editOpen} onClose={() => setEditOpen(false)} title="Edit personal info">
        <BasicInfoForm
          defaultValues={p}
          onSubmit={(data: any) => profileMut.mutate(data)}
          loading={profileMut.isPending}
        />
      </Modal>
    </div>
  )
}
