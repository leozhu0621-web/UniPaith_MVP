/**
 * Journey checklist (UX overhaul Ship C §3) — My Space home card consuming the
 * existing 13-step `GET /students/me/onboarding` progress engine
 * (student_service.get_onboarding_status). Imprint progress language: an
 * animated gold progress ring (same double-rAF dashoffset pattern as DualRing),
 * the next 3 incomplete steps as stagger-list rows deep-linking into the
 * Profile tabs that complete them, and completed steps collapsed into a
 * "N done" pill. Hides itself entirely at 100% — established students never
 * see setup chrome.
 */
import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { ArrowRight, CheckCircle2, ListChecks } from 'lucide-react'

import Card from '../../../components/ui/Card'
import { ListRow } from '../../../components/student/density'
import { getOnboarding } from '../../../api/students'
import { prefersReducedMotion, useCountUp } from '../../../hooks/useCountUp'
import { track } from '../../../lib/analytics'
import type { OnboardingStatus } from '../../../types'

// The engine's step keys, in its own completion order, mapped to the route
// where each step gets done. Every target exists in App.tsx: /s/profile renders
// ProfilePage whose ?tab= values come from PROFILE_TABS_SPEC (overview ·
// academics · experience · goals · preferences). Test scores, languages and
// research are sections of the Academics tab; activities, links, portfolio,
// work and competitions are sections of the Experience tab.
const STEP_SPECS: { key: string; label: string; sub: string; to: string }[] = [
  { key: 'basic_profile', label: 'Add your basic info', sub: 'Name and nationality unlock everything else', to: '/s/profile' },
  { key: 'academics', label: 'Add an academic record', sub: 'Match scores improve once we know your grades', to: '/s/profile?tab=academics' },
  { key: 'test_scores', label: 'Add a test score', sub: 'SAT, GRE, IELTS — whatever you have', to: '/s/profile?tab=academics' },
  { key: 'activities', label: 'Add an activity', sub: 'Clubs, projects, anything you give time to', to: '/s/profile?tab=experience' },
  { key: 'online_presence', label: 'Link your LinkedIn or portfolio', sub: 'Links strengthen your other entries', to: '/s/profile?tab=experience' },
  { key: 'portfolio', label: 'Showcase a project', sub: 'A work sample makes your story concrete', to: '/s/profile?tab=experience' },
  { key: 'research', label: 'Add research experience', sub: 'Labs, papers, independent projects', to: '/s/profile?tab=academics' },
  { key: 'languages', label: 'Add the languages you speak', sub: 'Programs care about language fit', to: '/s/profile?tab=academics' },
  { key: 'work_experience', label: 'Add work or volunteer experience', sub: 'Internships and jobs count', to: '/s/profile?tab=experience' },
  { key: 'competitions', label: 'Add a competition', sub: 'Olympiads, hackathons, case comps', to: '/s/profile?tab=experience' },
  { key: 'goals', label: 'Describe your goals', sub: 'Sharpens your strategy and rationales', to: '/s/profile?tab=goals' },
  { key: 'preferences', label: 'Set program preferences', sub: 'Location, budget and format filter your matches', to: '/s/profile?tab=preferences' },
]

/** Gold progress ring — mounts empty, then a double rAF flips `drawn` so the
 *  0.8s dashoffset transition plays the initial fill (DualRing's pattern).
 *  Reduced motion mounts pre-drawn; the numeral counts up alongside. */
function ProgressRing({ pct, size = 64, stroke = 6 }: { pct: number; size?: number; stroke?: number }) {
  const [drawn, setDrawn] = useState(() => prefersReducedMotion())
  useEffect(() => {
    if (drawn) return
    let raf2 = 0
    const raf1 = requestAnimationFrame(() => {
      raf2 = requestAnimationFrame(() => setDrawn(true))
    })
    return () => {
      cancelAnimationFrame(raf1)
      cancelAnimationFrame(raf2)
    }
  }, [drawn])

  const counted = useCountUp(pct)
  const r = (size - stroke) / 2
  const c = 2 * Math.PI * r
  const offset = drawn ? c * (1 - pct / 100) : c

  return (
    <div className="relative flex-shrink-0" style={{ width: size, height: size }} aria-hidden>
      <svg width={size} height={size} className="-rotate-90" viewBox={`0 0 ${size} ${size}`}>
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="hsl(var(--border))" strokeWidth={stroke} />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          stroke="hsl(var(--primary))"
          strokeWidth={stroke}
          strokeDasharray={c}
          strokeDashoffset={offset}
          strokeLinecap="round"
          style={{ transition: 'stroke-dashoffset 0.8s ease-out' }}
        />
      </svg>
      <div className="absolute inset-0 flex items-center justify-center leading-none">
        <span className="text-base font-bold text-foreground tabular-nums">{counted}%</span>
      </div>
    </div>
  )
}

export default function JourneyChecklistCard({ className }: { className?: string }) {
  const navigate = useNavigate()
  // Key shared with OverviewTab's invalidation (`['onboarding']`), so finishing
  // a step from the profile refreshes this card on the next Home visit.
  const { data } = useQuery<OnboardingStatus>({
    queryKey: ['onboarding'],
    queryFn: getOnboarding,
    staleTime: 60_000,
  })

  // Quiet by design: no skeleton, no error chrome — the card simply appears
  // when the engine has something left to do, and vanishes at 100%.
  if (!data || data.completion_percentage >= 100) return null

  const done = new Set(data.steps_completed)
  const nextSteps = STEP_SPECS.filter(s => !done.has(s.key)).slice(0, 3)
  if (nextSteps.length === 0) return null

  const goTo = (step: { key: string; to: string }) => {
    // Open-union analytics event (Ship C §3 instrumentation).
    track('onboarding_checklist_step_clicked', { step: step.key, to: step.to })
    navigate(step.to)
  }

  return (
    <Card pad={false} className={`p-5 ${className ?? ''}`}>
      <div className="flex items-center gap-4">
        <ProgressRing pct={data.completion_percentage} />
        <div className="min-w-0 flex-1">
          <p className="text-sm font-semibold text-foreground flex items-center gap-1.5">
            <ListChecks size={15} className="text-secondary" aria-hidden /> Set up your space
          </p>
          <p className="text-xs text-muted-foreground mt-0.5">
            Each step sharpens your matches — pick up wherever you like.
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
            sub={step.sub}
            trailing={<ArrowRight size={14} className="text-secondary" aria-hidden />}
            onClick={() => goTo(step)}
          />
        ))}
      </div>
    </Card>
  )
}
