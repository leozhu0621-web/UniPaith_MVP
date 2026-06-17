import { useCallback, useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import clsx from 'clsx'
import { ArrowLeft, ArrowRight, Check, GraduationCap } from 'lucide-react'
import { getProfile, patchOnboardingState, type OnboardingStatePatch } from '../../api/students'
import type { OnboardingAnswers } from '../../types'
import usePageTitle from '../../hooks/usePageTitle'
import { prefersReducedMotion } from '../../hooks/useCountUp'
import { track } from '../../lib/analytics'
import Button from '../../components/ui/Button'
import OptionCard from './onboarding/OptionCard'
import {
  STAGE_OPTIONS,
  INTEREST_TRACKS,
  DEGREE_OPTIONS,
  BUDGET_OPTIONS,
  GEO_OPTIONS,
  nextIntakeTerms,
} from './onboarding/catalog'
import {
  clearLocalDraft,
  mergeWithLocalDraft,
  writeLocalDraft,
} from './onboarding/onboarding-state'

/**
 * Full-scale onboarding (UX overhaul Ship C §3) — Imprint-style wizard.
 *
 * ONE question per screen, big tappable option cards, segmented progress on
 * top, slide step transitions, skippable but never lost: every answer
 * autosaves via PATCH /students/me/onboarding/state (optimistic; failures fall
 * back to the localStorage draft so a frontend-first deploy or flaky network
 * never loses answers), and mount resumes from onboarding_state.last_step.
 *
 * Renders OUTSIDE StudentLayout (own full-screen chrome — see App.tsx
 * /onboarding route). Entry routing lives in pages/auth/* + the needs-rule in
 * onboarding/onboarding-state.ts.
 */

const STEP_KEYS = ['welcome', 'stage', 'interests', 'degree_level', 'intake_term', 'constraints', 'setup'] as const
const LAST_STEP = STEP_KEYS.length - 1
const INTAKE_TERMS = nextIntakeTerms(6)

type Direction = 'forward' | 'back'

export default function OnboardingPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  usePageTitle('Welcome')

  const profileQ = useQuery({ queryKey: ['profile'], queryFn: getProfile })

  const [ready, setReady] = useState(false)
  const [step, setStep] = useState(0)
  const [direction, setDirection] = useState<Direction>('forward')
  const [answers, setAnswers] = useState<OnboardingAnswers>({})
  const answersRef = useRef(answers)
  answersRef.current = answers
  const advanceTimer = useRef<ReturnType<typeof setTimeout> | null>(null)
  const completedRef = useRef(false)

  // ── Resume: hydrate once from server state merged with the local draft ──
  useEffect(() => {
    if (ready || profileQ.isPending) return
    const merged = mergeWithLocalDraft(profileQ.data?.onboarding_state)
    setAnswers(merged.answers ?? {})
    const resumeStep = Math.min(Math.max(merged.last_step ?? 0, 0), LAST_STEP)
    // Never resume INTO the celebration screen unless actually completed.
    setStep(merged.completed_at ? resumeStep : Math.min(resumeStep, LAST_STEP - 1))
    if (merged.last_step == null && !merged.completed_at) track('onboarding_started')
    setReady(true)
  }, [ready, profileQ.isPending, profileQ.data])

  useEffect(() => () => {
    if (advanceTimer.current) clearTimeout(advanceTimer.current)
  }, [])

  // ── Persistence: optimistic, full-state, failure-tolerant ──
  // Always send the FULL answer set (server merges key-wise, so this is
  // idempotent and makes any later successful PATCH self-healing). The local
  // draft mirrors every write; it is only cleared once a TERMINAL patch
  // (completed/dismissed) lands on the server.
  const persist = useCallback((overrides: Partial<OnboardingStatePatch> = {}, lastStep?: number) => {
    const patch: OnboardingStatePatch = {
      answers: answersRef.current,
      ...(lastStep !== undefined ? { last_step: lastStep } : {}),
      ...overrides,
    }
    writeLocalDraft(patch)
    patchOnboardingState(patch)
      .then(() => {
        if (patch.completed || patch.dismissed) {
          clearLocalDraft()
          void queryClient.invalidateQueries({ queryKey: ['profile'] })
        }
      })
      .catch(() => {
        /* tolerated — the local draft is the fallback; retried implicitly by
           the next full-state PATCH */
      })
  }, [queryClient])

  const goTo = useCallback((next: number, dir: Direction) => {
    if (advanceTimer.current) {
      clearTimeout(advanceTimer.current)
      advanceTimer.current = null
    }
    if (dir === 'forward') track('onboarding_step_completed', { step: STEP_KEYS[step] })
    setDirection(dir)
    setStep(next)
    persist({}, next)
  }, [persist, step])

  // Autosave on every answer change ("skippable but never lost"): single-select
  // steps would otherwise only save when the advance timer fires, and
  // multi-select steps (interests/geos/budget) never until Continue/Skip — a
  // refresh in that window dropped in-progress answers from state + draft.
  const updateAnswers = useCallback((next: OnboardingAnswers) => {
    answersRef.current = next
    setAnswers(next)
    persist({ answers: next })
  }, [persist])

  /** Single-select: stamp the answer, beat, then slide on (Imprint rhythm). */
  const chooseAndAdvance = useCallback(<K extends keyof OnboardingAnswers>(key: K, value: OnboardingAnswers[K], fromStep: number) => {
    updateAnswers({ ...answersRef.current, [key]: value })
    if (advanceTimer.current) clearTimeout(advanceTimer.current)
    const delay = prefersReducedMotion() ? 0 : 350
    advanceTimer.current = setTimeout(() => goTo(fromStep + 1, 'forward'), delay)
  }, [goTo, updateAnswers])

  const toggleInList = useCallback((key: 'interests' | 'geos', value: string) => {
    const list = answersRef.current[key] ?? []
    updateAnswers({
      ...answersRef.current,
      [key]: list.includes(value) ? list.filter((v) => v !== value) : [...list, value],
    })
  }, [updateAnswers])

  const dismiss = useCallback(() => {
    track('onboarding_skipped', { step: STEP_KEYS[step] })
    persist({ dismissed: true }, step)
    navigate('/s', { replace: true })
  }, [navigate, persist, step])

  // ── Completion: entering the final screen stamps completed (idempotent) ──
  useEffect(() => {
    if (!ready || step !== LAST_STEP || completedRef.current) return
    completedRef.current = true
    track('onboarding_completed')
    persist({ completed: true }, LAST_STEP)
  }, [ready, step, persist])

  // ── Keyboard: number keys select options; Enter continues (welcome). ──
  const onKeyDown = useCallback((e: React.KeyboardEvent<HTMLDivElement>) => {
    if (e.key >= '1' && e.key <= '9') {
      const idx = Number(e.key) - 1
      if (step === 1 && STAGE_OPTIONS[idx]) chooseAndAdvance('stage', STAGE_OPTIONS[idx].value, 1)
      else if (step === 2 && INTEREST_TRACKS[idx]) toggleInList('interests', INTEREST_TRACKS[idx].value)
      else if (step === 3 && DEGREE_OPTIONS[idx]) chooseAndAdvance('degree_level', DEGREE_OPTIONS[idx].value, 3)
      else if (step === 4 && INTAKE_TERMS[idx]) chooseAndAdvance('intake_term', INTAKE_TERMS[idx], 4)
      else if (step === 5 && BUDGET_OPTIONS[idx]) updateAnswers({ ...answersRef.current, budget_band: BUDGET_OPTIONS[idx].value })
    } else if (e.key === 'Enter' && e.target === e.currentTarget) {
      if (step === 0) goTo(1, 'forward')
      else if (step === 2 || step === 5) goTo(step + 1, 'forward')
    }
  }, [step, chooseAndAdvance, toggleInList, goTo, updateAnswers])

  if (!ready) {
    return (
      <div className="min-h-dvh bg-background flex items-center justify-center p-6">
        <div className="w-full max-w-xl space-y-4" aria-busy="true" aria-label="Loading onboarding">
          <div className="up-skeleton h-2 w-full rounded-full" />
          <div className="up-skeleton h-8 w-2/3 rounded-lg" />
          <div className="up-skeleton h-24 w-full rounded-xl" />
          <div className="up-skeleton h-24 w-full rounded-xl" />
        </div>
      </div>
    )
  }

  const firstName: string = profileQ.data?.first_name || profileQ.data?.preferred_name || ''
  const showSkipLink = step >= 1 && step < LAST_STEP

  return (
    <div className="min-h-dvh bg-background flex flex-col" onKeyDown={onKeyDown} tabIndex={-1}>
      {/* Header — wordmark · segmented progress · "Do this later" */}
      <header className="px-4 sm:px-6 pt-4 sm:pt-5">
        <div className="mx-auto w-full max-w-xl">
          <div className="flex items-center justify-between gap-4 mb-4">
            <span className="inline-flex items-center gap-2 text-sm font-bold text-foreground">
              <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-secondary/10 text-secondary">
                <GraduationCap size={16} />
              </span>
              UniPaith
            </span>
            {step < LAST_STEP && (
              <button
                type="button"
                onClick={dismiss}
                className="text-xs font-medium text-muted-foreground hover:text-foreground transition-colors rounded focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              >
                Do this later
              </button>
            )}
          </div>
          {/* Segmented progress — one segment per step, animated fill. */}
          <div
            className="flex items-center gap-1.5"
            role="progressbar"
            aria-valuemin={1}
            aria-valuemax={STEP_KEYS.length}
            aria-valuenow={step + 1}
            aria-label={`Step ${step + 1} of ${STEP_KEYS.length}`}
          >
            {STEP_KEYS.map((key, i) => (
              <span key={key} className="relative h-1.5 flex-1 overflow-hidden rounded-full bg-border">
                <span
                  className={clsx(
                    'absolute inset-0 origin-left rounded-full bg-secondary transition-transform duration-500',
                    i <= step ? 'scale-x-100' : 'scale-x-0'
                  )}
                  style={{ transitionTimingFunction: 'var(--ease-out)' }}
                />
              </span>
            ))}
          </div>
        </div>
      </header>

      {/* Step body — keyed remount drives the slide transition. */}
      <main className="flex-1 flex flex-col px-4 sm:px-6 py-8 overflow-x-clip">
        <div
          key={step}
          className={clsx(
            'mx-auto w-full max-w-xl flex-1 flex flex-col',
            direction === 'forward' ? 'animate-slide-in-right' : 'animate-slide-in-left'
          )}
        >
          {step === 0 && (
            <StepShell
              title={firstName ? `Let's set up your space, ${firstName}` : "Let's set up your space"}
              subtitle="A few taps to personalize your matches and deadlines."
              center
            >
              <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-secondary/10 text-secondary mb-2 animate-scale-in">
                <GraduationCap size={30} />
              </div>
              <Button size="lg" className="w-full" onClick={() => goTo(1, 'forward')} autoFocus>
                Get started <ArrowRight size={18} />
              </Button>
            </StepShell>
          )}

          {step === 1 && (
            <StepShell title="What stage are you at?" subtitle="This shapes what we show you first.">
              <div className="grid gap-3" role="radiogroup" aria-label="Journey stage">
                {STAGE_OPTIONS.map((o) => (
                  <OptionCard
                    key={o.value}
                    label={o.label}
                    hint={o.hint}
                    icon={o.icon}
                    selected={answers.stage === o.value}
                    onSelect={() => chooseAndAdvance('stage', o.value, 1)}
                  />
                ))}
              </div>
            </StepShell>
          )}

          {step === 2 && (
            <StepShell title="Which fields interest you?" subtitle="Pick as many as you like.">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 stagger-list" role="group" aria-label="Fields of interest">
                {INTEREST_TRACKS.map((o) => (
                  <OptionCard
                    key={o.value}
                    label={o.label}
                    icon={o.icon}
                    multi
                    size="chip"
                    selected={(answers.interests ?? []).includes(o.value)}
                    onSelect={() => toggleInList('interests', o.value)}
                  />
                ))}
              </div>
              <Button
                size="lg"
                className="w-full mt-6"
                disabled={(answers.interests ?? []).length === 0}
                onClick={() => goTo(3, 'forward')}
              >
                Continue
                {(answers.interests ?? []).length > 0 && ` · ${(answers.interests ?? []).length} selected`}
                <ArrowRight size={18} />
              </Button>
            </StepShell>
          )}

          {step === 3 && (
            <StepShell title="What degree level?">
              <div className="grid gap-3 sm:grid-cols-2" role="radiogroup" aria-label="Degree level">
                {DEGREE_OPTIONS.map((o) => (
                  <OptionCard
                    key={o.value}
                    label={o.label}
                    hint={o.hint}
                    icon={o.icon}
                    selected={answers.degree_level === o.value}
                    onSelect={() => chooseAndAdvance('degree_level', o.value, 3)}
                  />
                ))}
              </div>
            </StepShell>
          )}

          {step === 4 && (
            <StepShell title="When do you want to start?" subtitle="Your target intake sets the deadline clock.">
              <div className="grid gap-3 sm:grid-cols-2" role="radiogroup" aria-label="Target intake term">
                {INTAKE_TERMS.map((term) => (
                  <OptionCard
                    key={term}
                    label={term}
                    selected={answers.intake_term === term}
                    onSelect={() => chooseAndAdvance('intake_term', term, 4)}
                  />
                ))}
              </div>
            </StepShell>
          )}

          {step === 5 && (
            <StepShell title="Any constraints to respect?" subtitle="Both optional.">
              <div className="space-y-6">
                <fieldset>
                  <legend className="text-xs font-semibold uppercase tracking-wide text-muted-foreground mb-2.5">
                    Yearly budget
                  </legend>
                  <div className="grid gap-2" role="radiogroup" aria-label="Budget band">
                    {BUDGET_OPTIONS.map((o) => (
                      <OptionCard
                        key={o.value}
                        label={o.label}
                        hint={o.hint}
                        size="chip"
                        selected={answers.budget_band === o.value}
                        onSelect={() =>
                          updateAnswers({
                            ...answersRef.current,
                            budget_band: answersRef.current.budget_band === o.value ? null : o.value,
                          })
                        }
                      />
                    ))}
                  </div>
                </fieldset>
                <fieldset>
                  <legend className="text-xs font-semibold uppercase tracking-wide text-muted-foreground mb-2.5">
                    Places you&apos;d consider
                  </legend>
                  <div className="flex flex-wrap gap-2" role="group" aria-label="Preferred geographies">
                    {GEO_OPTIONS.map((geo) => {
                      const on = (answers.geos ?? []).includes(geo)
                      return (
                        <button
                          key={geo}
                          type="button"
                          role="checkbox"
                          aria-checked={on}
                          onClick={() => toggleInList('geos', geo)}
                          style={{ transitionTimingFunction: 'var(--ease-spring)' }}
                          className={clsx(
                            'inline-flex items-center gap-1.5 rounded-full border px-3.5 py-2 text-[13px] font-medium transition-all duration-200 active:scale-95',
                            'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring',
                            on
                              ? 'border-secondary bg-secondary text-secondary-foreground'
                              : 'border-border bg-card text-foreground hover:border-secondary/40'
                          )}
                        >
                          {on && <Check size={13} strokeWidth={3} />}
                          {geo}
                        </button>
                      )
                    })}
                  </div>
                </fieldset>
              </div>
              <Button size="lg" className="w-full mt-8" onClick={() => goTo(6, 'forward')}>
                {answers.budget_band || (answers.geos ?? []).length > 0 ? 'Continue' : 'No constraints — continue'}
                <ArrowRight size={18} />
              </Button>
            </StepShell>
          )}

          {step === 6 && (
            <BuildMoment
              answers={answers}
              onTalkToUni={() => navigate('/s', { replace: true })}
              onExplore={() => navigate('/s/explore', { replace: true })}
            />
          )}

          {/* Footer — back + per-step skip ("skippable but never lost"). */}
          {step > 0 && step < LAST_STEP && (
            <div className="mt-auto pt-8 flex items-center justify-between">
              <button
                type="button"
                onClick={() => goTo(step - 1, 'back')}
                className="inline-flex items-center gap-1.5 text-sm font-medium text-muted-foreground hover:text-foreground transition-colors rounded focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              >
                <ArrowLeft size={16} /> Back
              </button>
              {showSkipLink && (
                <button
                  type="button"
                  onClick={() => goTo(step + 1, 'forward')}
                  className="text-sm text-muted-foreground hover:text-foreground transition-colors rounded focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                >
                  Skip for now
                </button>
              )}
            </div>
          )}
        </div>
      </main>
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────

function StepShell({
  title,
  subtitle,
  center = false,
  children,
}: {
  title: string
  subtitle?: string
  center?: boolean
  children: React.ReactNode
}) {
  return (
    <div className={clsx('flex flex-col gap-6', center && 'flex-1 justify-center text-center')}>
      <div className={clsx('space-y-2', center && 'mx-auto max-w-md')}>
        <h1 className="text-2xl font-bold text-foreground text-balance">{title}</h1>
        {subtitle && <p className="text-[15px] text-muted-foreground leading-relaxed">{subtitle}</p>}
      </div>
      {children}
    </div>
  )
}

/** Step 7 — "Setting up your space": ring fill + staggered checklist → CTAs. */
function BuildMoment({
  answers,
  onTalkToUni,
  onExplore,
}: {
  answers: OnboardingAnswers
  onTalkToUni: () => void
  onExplore: () => void
}) {
  const [filled, setFilled] = useState(false)
  const [showCtas, setShowCtas] = useState(false)

  useEffect(() => {
    if (prefersReducedMotion()) {
      setFilled(true)
      setShowCtas(true)
      return
    }
    // rAF so the ring's 0% state paints first, then the dashoffset transitions.
    const raf = requestAnimationFrame(() => setFilled(true))
    const timer = setTimeout(() => setShowCtas(true), 1300)
    return () => {
      cancelAnimationFrame(raf)
      clearTimeout(timer)
    }
  }, [])

  const stageLabel = STAGE_OPTIONS.find((o) => o.value === answers.stage)?.label
  const degreeLabel = DEGREE_OPTIONS.find((o) => o.value === answers.degree_level)?.label
  const interestCount = (answers.interests ?? []).length
  const personalized: string[] = [
    stageLabel ? `Stage: ${stageLabel.toLowerCase()}` : 'Stage set with Uni',
    interestCount > 0
      ? `${interestCount} field${interestCount === 1 ? '' : 's'} added to matching`
      : 'Interests open — Uni will help you find them',
    degreeLabel ? `Matching ${degreeLabel} programs` : 'Degree level open — Uni will help you pick',
    answers.intake_term ? `Deadlines tracked for ${answers.intake_term}` : 'Timeline flexible for now',
    answers.budget_band || (answers.geos ?? []).length > 0
      ? 'Budget and location saved'
      : 'No constraints set',
  ]

  const SIZE = 120
  const STROKE = 8
  const r = (SIZE - STROKE) / 2
  const c = 2 * Math.PI * r

  return (
    <div className="flex-1 flex flex-col justify-center text-center gap-7">
      <div className="relative mx-auto animate-beat rounded-full" style={{ width: SIZE, height: SIZE }}>
        <svg width={SIZE} height={SIZE} className="-rotate-90">
          <circle cx={SIZE / 2} cy={SIZE / 2} r={r} fill="none" stroke="currentColor" strokeWidth={STROKE} className="text-border" />
          <circle
            cx={SIZE / 2}
            cy={SIZE / 2}
            r={r}
            fill="none"
            stroke="currentColor"
            strokeWidth={STROKE}
            strokeLinecap="round"
            strokeDasharray={c}
            strokeDashoffset={filled ? 0 : c}
            className="text-primary"
            style={{ transition: 'stroke-dashoffset 1.1s var(--ease-out)' }}
          />
        </svg>
        <span className="absolute inset-0 flex items-center justify-center text-secondary">
          <GraduationCap size={36} />
        </span>
      </div>

      <div className="space-y-2">
        <h1 className="text-lg font-bold text-foreground">Your space is ready</h1>
        <p className="text-[15px] text-muted-foreground">Here&apos;s what we personalized:</p>
      </div>

      <ul className="stagger-list mx-auto w-full max-w-sm space-y-2.5 text-left">
        {personalized.map((line) => (
          <li key={line} className="flex items-start gap-2.5 text-sm text-foreground">
            <span className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-primary/15 text-foreground">
              <Check size={12} strokeWidth={3} />
            </span>
            {line}
          </li>
        ))}
      </ul>

      <div
        className={clsx(
          'mx-auto w-full max-w-sm space-y-3 transition-opacity duration-300',
          showCtas ? 'opacity-100 animate-slide-up-fade' : 'opacity-0 pointer-events-none'
        )}
      >
        <Button variant="primary" size="lg" className="w-full" onClick={onTalkToUni}>
          Talk to Uni <ArrowRight size={18} />
        </Button>
        <Button variant="tertiary" size="lg" className="w-full" onClick={onExplore}>
          Explore matches
        </Button>
      </div>
    </div>
  )
}
