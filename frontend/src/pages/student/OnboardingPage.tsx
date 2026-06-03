import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import clsx from 'clsx'
import { updateProfile } from '../../api/students'
import { startSession } from '../../api/discovery'
import usePageTitle from '../../hooks/usePageTitle'
import Button from '../../components/ui/Button'
import Input from '../../components/ui/Input'
import {
  GraduationCap,
  Compass,
  Target,
  ClipboardList,
  ArrowRight,
  ArrowLeft,
  Check,
} from 'lucide-react'

/**
 * Student onboarding — "Welcome + orient → Discover".
 *
 * Three short steps: a warm welcome, a how-it-works orientation (Discover →
 * Match → Apply), then a light personalization (first name + what they're
 * exploring). On finish we persist the answers to the profile (PUT
 * /me/profile, which also advances onboarding_progress), seed the first
 * Discover session, and route into Discover at track=profile, layer=basic.
 *
 * Reached when a brand-new student lands (AuthCallbackPage routes new
 * students here). Nothing is forced — "Skip for now" jumps straight to
 * Discover, and a save failure never blocks entry.
 */

const TOTAL_STEPS = 3

const STAGES = [
  {
    icon: Compass,
    title: 'Discover',
    body: 'Tell us about you in a short conversation — no dreaded forms. We learn your profile, goals, and what matters to you.',
  },
  {
    icon: Target,
    title: 'Match',
    body: 'See programs ranked by real fit, each with a confidence score so you know how sure we are.',
  },
  {
    icon: ClipboardList,
    title: 'Apply',
    body: 'Stay on top of deadlines, tasks, and essay feedback — all the way to decision day.',
  },
]

const DEGREE_LEVELS = ["Bachelor's", "Master's", 'PhD / Doctorate', 'Not sure yet']

export default function OnboardingPage() {
  const navigate = useNavigate()
  usePageTitle('Welcome')

  const [step, setStep] = useState(0)
  const [firstName, setFirstName] = useState('')
  const [degree, setDegree] = useState<string | null>(null)
  const [field, setField] = useState('')

  const goToDiscover = () => navigate('/s?track=profile&layer=basic', { replace: true })

  const finishMut = useMutation({
    mutationFn: async () => {
      const payload: Record<string, string> = {}
      const name = firstName.trim()
      if (name) {
        payload.first_name = name
        payload.preferred_name = name
      }
      if (degree && degree !== 'Not sure yet') {
        const f = field.trim()
        payload.goals_text = f
          ? `Exploring ${degree} programs in ${f}.`
          : `Exploring ${degree} programs.`
      } else if (field.trim()) {
        payload.goals_text = `Interested in ${field.trim()}.`
      }
      // Persist what we collected — but never block entry on a save failure.
      if (Object.keys(payload).length > 0) {
        try {
          await updateProfile(payload)
        } catch {
          /* non-blocking — they can fill this in via Profile later */
        }
      }
      // Seed the first Discover conversation (Discover also self-seeds on arrival).
      try {
        await startSession('profile', 'basic')
      } catch {
        /* non-blocking */
      }
    },
    onSettled: goToDiscover,
  })

  return (
    <div className="min-h-screen bg-background flex flex-col">
      <main className="flex-1 flex items-center justify-center px-6 py-12">
        <div className="w-full max-w-lg">
          {/* Progress */}
          <div className="flex items-center gap-2 mb-10" aria-label={`Step ${step + 1} of ${TOTAL_STEPS}`}>
            {Array.from({ length: TOTAL_STEPS }).map((_, i) => (
              <span
                key={i}
                className={clsx(
                  'h-1 flex-1 rounded-full transition-colors duration-300',
                  i <= step ? 'bg-secondary' : 'bg-border'
                )}
              />
            ))}
          </div>

          {/* Step 0 — Welcome */}
          {step === 0 && (
            <div className="text-center space-y-6">
              <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-secondary/10 text-secondary">
                <GraduationCap size={28} />
              </div>
              <div className="space-y-3">
                <h1 className="text-2xl font-bold text-foreground">Welcome to UniPaith</h1>
                <p className="text-base text-muted-foreground leading-relaxed">
                  Your AI guide from “where do I even start?” to the right programs — with a
                  real plan to get in.
                </p>
              </div>
              <div className="space-y-3 pt-2">
                <Button size="lg" className="w-full" onClick={() => setStep(1)}>
                  Get started <ArrowRight size={18} />
                </Button>
                <button
                  type="button"
                  onClick={goToDiscover}
                  className="text-sm text-muted-foreground hover:text-foreground transition-colors"
                >
                  Skip for now
                </button>
              </div>
            </div>
          )}

          {/* Step 1 — How it works */}
          {step === 1 && (
            <div className="space-y-8">
              <div className="text-center space-y-2">
                <h2 className="text-xl font-bold text-foreground">How UniPaith works</h2>
                <p className="text-sm text-muted-foreground">Three stages, one continuous journey.</p>
              </div>
              <ol className="space-y-4">
                {STAGES.map((s, i) => (
                  <li key={s.title} className="flex gap-4 rounded-xl border border-border bg-card p-4">
                    <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-secondary/10 text-secondary">
                      <s.icon size={20} />
                    </div>
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                          Step {i + 1}
                        </span>
                        <h3 className="text-sm font-bold text-foreground">{s.title}</h3>
                      </div>
                      <p className="text-sm text-muted-foreground leading-relaxed">{s.body}</p>
                    </div>
                  </li>
                ))}
              </ol>
              <div className="flex items-center gap-3">
                <Button variant="ghost" onClick={() => setStep(0)}>
                  <ArrowLeft size={18} /> Back
                </Button>
                <Button className="flex-1" onClick={() => setStep(2)}>
                  Next <ArrowRight size={18} />
                </Button>
              </div>
            </div>
          )}

          {/* Step 2 — Personalize */}
          {step === 2 && (
            <div className="space-y-6">
              <div className="text-center space-y-2">
                <h2 className="text-xl font-bold text-foreground">Let’s personalize your start</h2>
                <p className="text-sm text-muted-foreground">
                  A couple quick things — you can change these anytime in your profile.
                </p>
              </div>
              <div className="space-y-5">
                <Input
                  label="What should we call you?"
                  value={firstName}
                  onChange={(e) => setFirstName(e.target.value)}
                  placeholder="First name"
                  autoFocus
                  maxLength={100}
                />
                <div>
                  <span className="block text-[13px] font-semibold text-muted-foreground mb-1.5">
                    What level are you exploring?
                  </span>
                  <div className="grid grid-cols-2 gap-2">
                    {DEGREE_LEVELS.map((d) => (
                      <button
                        key={d}
                        type="button"
                        aria-pressed={degree === d}
                        onClick={() => setDegree(d === degree ? null : d)}
                        className={clsx(
                          'rounded-lg border px-3 py-2.5 text-sm font-medium text-left transition-colors',
                          'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring',
                          degree === d
                            ? 'border-secondary bg-secondary/10 text-secondary'
                            : 'border-border bg-card text-foreground hover:bg-muted'
                        )}
                      >
                        <span className="inline-flex items-center gap-1.5">
                          {degree === d && <Check size={14} />}
                          {d}
                        </span>
                      </button>
                    ))}
                  </div>
                </div>
                <Input
                  label="Field or area of interest (optional)"
                  value={field}
                  onChange={(e) => setField(e.target.value)}
                  placeholder="e.g. Computer Science, Public Health"
                  maxLength={120}
                />
              </div>
              <div className="flex items-center gap-3">
                <Button variant="ghost" onClick={() => setStep(1)} disabled={finishMut.isPending}>
                  <ArrowLeft size={18} /> Back
                </Button>
                <Button
                  variant="primary"
                  className="flex-1"
                  loading={finishMut.isPending}
                  onClick={() => finishMut.mutate()}
                >
                  Start exploring <ArrowRight size={18} />
                </Button>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  )
}
