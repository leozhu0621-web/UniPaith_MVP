/**
 * Profile → Overview tab (Spec/08 §4).
 *
 * Personal header (Section 1) + completion map (cluster cards) + the
 * "What's next" action queue derived from completion gaps + onboarding.
 */
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { ArrowRight, Pencil } from 'lucide-react'

import Button from '../../../components/ui/Button'
import Card from '../../../components/ui/Card'
import Modal from '../../../components/ui/Modal'
import { SkeletonCard } from '../../../components/ui/Skeleton'
import { getNextStep, getProfile, updateProfile } from '../../../api/students'
import { listDocuments } from '../../../api/documents'
import { useAuthStore } from '../../../stores/auth-store'
import { showToast } from '../../../stores/toast-store'
import { initials } from '../../../utils/format'
import { DEGREE_LABELS } from '../../../utils/constants'
import { BasicInfoForm } from '../components/ProfileForms'
import { useCompletion } from './useCompletion'
import { ConfidenceDots, lastUpdatedLabel, CATEGORY_META, type CategoryKey } from './shared'

interface NextAction {
  action: string
  reason: string
  tab: CategoryKey | 'data'
  cta: string
}

function deriveNextActions(
  stats: ReturnType<typeof useCompletion>['stats'],
  profile: any,
  documentsCount: number,
  nextGuidance: string | null,
): NextAction[] {
  const out: NextAction[] = []
  const by = (k: CategoryKey) => stats.find(s => s.key === k)

  if ((profile?.academic_records ?? []).length === 0)
    out.push({
      action: 'Add an academic record',
      reason: 'Match scores improve once we know your grades.',
      tab: 'academics',
      cta: 'Add',
    })
  if (documentsCount === 0)
    out.push({
      action: 'Upload an unofficial transcript',
      reason: 'Programs weigh your coursework — a transcript strengthens every match.',
      tab: 'preparation',
      cta: 'Upload',
    })
  if ((profile?.online_presence ?? []).length === 0)
    out.push({
      action: 'Connect your LinkedIn',
      reason: 'Links strengthen your activity and work entries.',
      tab: 'experience',
      cta: 'Connect',
    })
  if ((by('goals')?.pct ?? 0) < 100)
    out.push({
      action: 'Round out your goals',
      reason: 'A goal in each area — academic, social, personal — sharpens your strategy.',
      tab: 'goals',
      cta: 'Add',
    })
  if ((by('identity')?.pct ?? 0) < 100)
    out.push({
      action: 'Deepen your identity layer',
      reason: 'Values and worldview personalize your matches and rationales.',
      tab: 'identity',
      cta: 'Open',
    })
  if ((by('preferences')?.pct ?? 0) < 100)
    out.push({
      action: 'Set your preferences',
      reason: 'Location, size, and format help us filter to programs that fit your life.',
      tab: 'preferences',
      cta: 'Set',
    })

  if (out.length === 0 && nextGuidance)
    out.push({ action: nextGuidance, reason: 'Suggested by your counselor.', tab: 'overview' as any, cta: 'Open' })

  return out.slice(0, 4)
}

export default function OverviewTab({ onOpenTab }: { onOpenTab: (tab: string) => void }) {
  const navigate = useNavigate()
  const qc = useQueryClient()
  const { user } = useAuthStore()
  const { data: profile, isLoading } = useQuery({ queryKey: ['profile'], queryFn: getProfile })
  const { data: nextStep } = useQuery({ queryKey: ['next-step'], queryFn: getNextStep })
  const { data: documents } = useQuery({ queryKey: ['documents'], queryFn: listDocuments })
  const { stats } = useCompletion()
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

  if (isLoading || !profile) {
    return (
      <div className="space-y-4">
        <SkeletonCard />
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <SkeletonCard key={i} />
          ))}
        </div>
      </div>
    )
  }

  const p: any = profile
  const documentsList: any[] = Array.isArray(documents) ? documents : []
  const fullName = [p.first_name, p.last_name].filter(Boolean).join(' ') || 'Your name'
  const latestAcademic = (p.academic_records ?? [])[0]
  const headline = latestAcademic
    ? [
        DEGREE_LABELS[latestAcademic.degree_type] || latestAcademic.degree_type,
        latestAcademic.field_of_study,
        latestAcademic.institution_name,
      ]
        .filter(Boolean)
        .join(' · ')
    : null
  const locationLine = [p.country_of_residence, p.nationality, p.preferred_pronouns ? `(${p.preferred_pronouns})` : null].filter(Boolean).join(' · ')
  const actions = deriveNextActions(stats, p, documentsList.length, nextStep?.guidance_text ?? null)

  return (
    <div className="space-y-8">
      {/* Personal header (Section 1) */}
      <Card className="p-6">
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

      {/* Completion map */}
      <section>
        <p className="up-eyebrow mb-3">Completion map</p>
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {stats.map(s => {
            const meta = CATEGORY_META.find(m => m.key === s.key)
            return (
              <Card key={s.key} className="p-4 flex flex-col gap-2" interactive onClick={() => onOpenTab(s.tab)}>
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-foreground">{s.label}</span>
                  <span className="text-sm font-bold text-foreground tabular-nums">{s.pct}%</span>
                </div>
                <ConfidenceDots filled={s.dots} showLabel={false} />
                {meta?.hint && (
                  <p className="text-xs text-muted-foreground">{meta.hint}</p>
                )}
                <div className="flex items-center justify-between mt-1">
                  <span className="text-xs text-muted-foreground">{lastUpdatedLabel(s.lastUpdated)}</span>
                  <span className="text-xs font-semibold text-secondary inline-flex items-center gap-0.5">
                    Open <ArrowRight size={12} />
                  </span>
                </div>
              </Card>
            )
          })}
        </div>
      </section>

      {/* Next-action queue */}
      <section>
        <p className="up-eyebrow mb-3">What's next</p>
        {actions.length === 0 ? (
          <Card className="p-5 space-y-2">
            <p className="text-sm text-foreground font-medium">Your profile is strong.</p>
            <p className="text-sm text-muted-foreground">
              Check in on your applications or explore new programs to keep momentum.
            </p>
            <div className="flex gap-3 pt-1">
              <button
                onClick={() => navigate('/s/applications')}
                className="text-sm font-semibold text-secondary hover:underline inline-flex items-center gap-1"
              >
                Applications <ArrowRight size={13} />
              </button>
              <button
                onClick={() => navigate('/s/explore')}
                className="text-sm font-semibold text-secondary hover:underline inline-flex items-center gap-1"
              >
                Explore programs <ArrowRight size={13} />
              </button>
            </div>
          </Card>
        ) : (
          <Card className="p-2">
            <ol className="divide-y divide-border">
              {actions.map((a, i) => (
                <li key={i} className="flex items-center gap-3 px-3 py-3">
                  <span className="h-6 w-6 shrink-0 rounded-full bg-muted text-foreground text-xs font-bold flex items-center justify-center">
                    {i + 1}
                  </span>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-foreground">{a.action}</p>
                    <p className="text-xs text-muted-foreground">{a.reason}</p>
                  </div>
                  <Button size="sm" variant="secondary" onClick={() => onOpenTab(a.tab)}>
                    {a.cta}
                  </Button>
                </li>
              ))}
            </ol>
          </Card>
        )}
      </section>

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
