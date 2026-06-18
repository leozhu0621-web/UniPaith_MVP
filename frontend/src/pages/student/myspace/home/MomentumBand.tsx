import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { ArrowRight, CheckCircle2, ListChecks } from 'lucide-react'

import Card from '../../../../components/ui/Card'
import { ListRow } from '../../../../components/student/density'
import { getOnboarding } from '../../../../api/students'
import { track } from '../../../../lib/analytics'
import type { OnboardingStatus } from '../../../../types'
import ProgressRing from './ProgressRing'
import JourneyMap from './JourneyMap'
import WeekRibbon from './WeekRibbon'
import type { StageInputs } from './journeyStage'
import type { WeekInputs } from './weekActivity'

// The onboarding engine's step keys mapped to the route that completes each
// (moved verbatim from the retired JourneyChecklistCard).
const STEP_SPECS: { key: string; label: string; to: string }[] = [
  { key: 'basic_profile', label: 'Add your basic info', to: '/s/profile' },
  { key: 'academics', label: 'Add an academic record', to: '/s/profile?tab=academics' },
  { key: 'test_scores', label: 'Add a test score', to: '/s/profile?tab=academics' },
  { key: 'activities', label: 'Add an activity', to: '/s/profile?tab=experience' },
  { key: 'online_presence', label: 'Link your LinkedIn or portfolio', to: '/s/profile?tab=experience' },
  { key: 'portfolio', label: 'Showcase a project', to: '/s/profile?tab=experience' },
  { key: 'research', label: 'Add research experience', to: '/s/profile?tab=academics' },
  { key: 'languages', label: 'Add the languages you speak', to: '/s/profile?tab=academics' },
  { key: 'work_experience', label: 'Add work or volunteer experience', to: '/s/profile?tab=experience' },
  { key: 'competitions', label: 'Add a competition', to: '/s/profile?tab=experience' },
  { key: 'goals', label: 'Describe your goals', to: '/s/profile?tab=goals' },
  { key: 'preferences', label: 'Set program preferences', to: '/s/profile?tab=preferences' },
]

interface Props {
  stage: StageInputs
  week: WeekInputs
  className?: string
}

/** Momentum band (Spec 2026-06-14 §Modules.2) — journey-stage map + this-week
 *  ribbon always render; the gold onboarding ring + next-3 setup steps appear
 *  only while onboarding < 100% (absorbs the retired JourneyChecklistCard). */
export default function MomentumBand({ stage, week, className }: Props) {
  const navigate = useNavigate()
  const { data } = useQuery<OnboardingStatus>({
    queryKey: ['onboarding'],
    queryFn: getOnboarding,
    staleTime: 60_000,
  })

  const pct = data?.completion_percentage ?? 100
  const showSetup = !!data && pct < 100
  const done = new Set(data?.steps_completed ?? [])
  const nextSteps = STEP_SPECS.filter(s => !done.has(s.key)).slice(0, 3)

  const goTo = (step: { key: string; to: string }) => {
    track('onboarding_checklist_step_clicked', { step: step.key, to: step.to })
    navigate(step.to)
  }

  return (
    <Card pad={false} className={`p-5 ${className ?? ''}`}>
      {/* Journey-stage map — always present. */}
      <JourneyMap {...stage} />

      {/* This-week ribbon — always present. */}
      <div className="mt-4">
        <WeekRibbon {...week} />
      </div>

      {/* Setup ring + next steps — only while onboarding is incomplete. */}
      {showSetup && nextSteps.length > 0 && (
        <div className="mt-4 border-t border-border pt-4">
          <div className="flex items-center gap-4">
            <ProgressRing pct={pct} />
            <div className="min-w-0 flex-1">
              <p className="flex items-center gap-1.5 text-sm font-semibold text-foreground">
                <ListChecks size={15} className="text-secondary" aria-hidden /> Set up your space
              </p>
            </div>
            {done.size > 0 && (
              <span className="inline-flex shrink-0 items-center gap-1 rounded-full bg-muted px-2 py-0.5 text-[11px] font-semibold text-muted-foreground">
                <CheckCircle2 size={12} className="text-success" aria-hidden /> {done.size} done
              </span>
            )}
          </div>
          <div className="stagger-list mt-3">
            {nextSteps.map(step => (
              <ListRow
                key={step.key}
                title={step.label}
                trailing={<ArrowRight size={14} className="text-secondary" aria-hidden />}
                onClick={() => goTo(step)}
              />
            ))}
          </div>
        </div>
      )}
    </Card>
  )
}
