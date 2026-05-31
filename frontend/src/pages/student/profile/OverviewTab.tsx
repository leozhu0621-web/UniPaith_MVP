/**
 * Profile → Overview tab (spec 10 §4).
 * PersonalHeader + CompletionMap (cluster cards) + NextActionQueue.
 * Driven by GET /students/me/profile/overview.
 */
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { ArrowRight } from 'lucide-react'

import { getProfileOverview, updateProfile } from '../../../api/students'
import Button from '../../../components/ui/Button'
import Card from '../../../components/ui/Card'
import Modal from '../../../components/ui/Modal'
import { SkeletonCard } from '../../../components/ui/Skeleton'
import { showToast } from '../../../stores/toast-store'
import type { ProfileOverview } from '../../../types'
import { BasicInfoForm } from '../components/ProfileForms'
import { DotMeter, relativeTime, useProfile } from './_shared'

const CATEGORY_LABEL: Record<string, string> = {
  identity: 'Identity',
  academics: 'Academics',
  experience: 'Experience',
  goals: 'Goals',
  needs: 'Needs',
  strategy: 'Strategy',
  preparation: 'Preparation',
  preferences: 'Preferences',
  financial: 'Financial',
  data: 'Data Rights',
}

function initials(first?: string | null, last?: string | null): string {
  const a = (first || '').trim()[0] || ''
  const b = (last || '').trim()[0] || ''
  return (a + b).toUpperCase() || '·'
}

export default function OverviewTab() {
  const navigate = useNavigate()
  const qc = useQueryClient()
  const { data: profile } = useProfile()
  const { data, isLoading, isError, refetch } = useQuery<ProfileOverview>({
    queryKey: ['profile-overview'],
    queryFn: getProfileOverview,
  })
  const [editOpen, setEditOpen] = useState(false)

  const editMut = useMutation({
    mutationFn: updateProfile,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['profile'] })
      qc.invalidateQueries({ queryKey: ['profile-overview'] })
      setEditOpen(false)
      showToast('Saved', 'success')
    },
    onError: () => showToast("Something didn't work. Try again.", 'error'),
  })

  if (isLoading) {
    return (
      <div className="space-y-4">
        <SkeletonCard />
        <SkeletonCard />
      </div>
    )
  }
  if (isError || !data) {
    return (
      <Card className="p-6 text-center">
        <p className="text-sm text-slate mb-3">We couldn't load your overview.</p>
        <Button variant="secondary" size="sm" onClick={() => refetch()}>
          Try again
        </Button>
      </Card>
    )
  }

  const { personal, completion, next_actions } = data
  const name = [personal.first_name, personal.last_name].filter(Boolean).join(' ') || 'Your profile'
  const metaLine = [personal.preferred_pronouns, personal.country_of_residence].filter(Boolean).join(' · ')

  return (
    <div className="space-y-6">
      {/* Personal header (spec §4 — Section 1, Personal) */}
      <Card className="p-5">
        <div className="flex items-start gap-4">
          <div className="w-20 h-20 rounded-full bg-student-mist flex items-center justify-center text-2xl font-semibold text-cobalt shrink-0">
            {initials(personal.first_name, personal.last_name)}
          </div>
          <div className="flex-1 min-w-0">
            <h2 className="text-lg font-semibold text-charcoal truncate">{name}</h2>
            {personal.primary_email && <p className="text-sm text-slate truncate">{personal.primary_email}</p>}
            {metaLine && <p className="text-sm text-slate mt-0.5">{metaLine}</p>}
            <button
              onClick={() => setEditOpen(true)}
              className="story-link text-sm text-cobalt mt-2 inline-block"
            >
              Edit personal info
            </button>
          </div>
        </div>
      </Card>

      {/* Completion map — one cluster card per fillable category */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
        {completion.per_category.map(cat => (
          <Card key={cat.category} className="p-4 flex flex-col gap-2">
            <div className="flex items-center justify-between">
              <span className="font-medium text-charcoal text-sm">
                {CATEGORY_LABEL[cat.category] ?? cat.category}
              </span>
              <span className="text-sm font-semibold text-charcoal tabular-nums">{cat.pct}%</span>
            </div>
            <DotMeter pct={cat.pct} />
            <span className="text-xs text-slate">Updated {relativeTime(cat.last_updated)}</span>
            <button
              onClick={() => navigate(`/s/profile?tab=${cat.category}`)}
              className="text-xs text-cobalt story-link self-start mt-1"
            >
              Open
            </button>
          </Card>
        ))}
      </div>

      {/* Next-action queue (spec §4 — "What's next") */}
      {next_actions.length > 0 && (
        <Card className="p-5">
          <h3 className="font-semibold text-charcoal mb-3">What's next</h3>
          <ol className="space-y-3">
            {next_actions.map((a, i) => (
              <li key={i} className="flex items-start justify-between gap-3">
                <div className="flex items-start gap-3 min-w-0">
                  <span className="text-sm font-semibold text-cobalt tabular-nums mt-0.5">{i + 1}</span>
                  <div className="min-w-0">
                    <p className="text-sm font-medium text-charcoal">{a.action}</p>
                    <p className="text-xs text-slate">{a.reason}</p>
                  </div>
                </div>
                <Button
                  size="sm"
                  variant="tertiary"
                  onClick={() => navigate(a.deep_link)}
                  className="shrink-0"
                >
                  Go <ArrowRight size={13} className="ml-1" />
                </Button>
              </li>
            ))}
          </ol>
        </Card>
      )}

      <Modal isOpen={editOpen} onClose={() => setEditOpen(false)} title="Edit personal info">
        <BasicInfoForm
          defaultValues={profile}
          onSubmit={d => editMut.mutate(d)}
          loading={editMut.isPending}
        />
      </Modal>
    </div>
  )
}
