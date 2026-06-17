/**
 * Profile → Basic info tab (key `overview`).
 *
 * Inline-editable basic record (2026-06-16) — a small avatar/name header plus
 * the BasicInfoForm rendered directly on the page (first/last name, pronouns,
 * DOB, nationality, country, bio, goals + Save). No read-only card, no modal.
 */
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import Card from '../../../components/ui/Card'
import { SkeletonCard } from '../../../components/ui/Skeleton'
import { getProfile, updateProfile } from '../../../api/students'
import { useAuthStore } from '../../../stores/auth-store'
import { showToast } from '../../../stores/toast-store'
import { initials } from '../../../utils/format'
import { BasicInfoForm } from '../components/ProfileForms'

export default function OverviewTab() {
  const qc = useQueryClient()
  const { user } = useAuthStore()
  const { data: profile, isLoading } = useQuery({ queryKey: ['profile'], queryFn: getProfile })

  const profileMut = useMutation({
    mutationFn: (data: any) => updateProfile(data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['profile'] })
      qc.invalidateQueries({ queryKey: ['onboarding'] })
      showToast('Saved', 'success')
    },
    onError: () => showToast("Something didn't work. Try again.", 'error'),
  })

  if (isLoading || !profile) return <SkeletonCard />

  const p: any = profile
  const fullName = [p.first_name, p.last_name].filter(Boolean).join(' ') || 'Your name'

  return (
    <div className="max-w-2xl space-y-5">
      <div className="flex items-center gap-4">
        <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-full bg-muted text-xl font-bold text-foreground">
          {initials(fullName)}
        </div>
        <div className="min-w-0">
          <p className="truncate text-base font-semibold text-foreground">{fullName}</p>
          {user?.email && <p className="truncate text-sm text-muted-foreground">{user.email}</p>}
        </div>
      </div>

      <Card pad={false} className="p-5">
        <BasicInfoForm
          defaultValues={p}
          onSubmit={(data: any) => profileMut.mutate(data)}
          loading={profileMut.isPending}
        />
      </Card>
    </div>
  )
}
