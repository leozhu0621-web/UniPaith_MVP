import { Check } from 'lucide-react'
import type { SetupStepsComplete } from '../../../types'

const SETUP_STEPS: { key: keyof SetupStepsComplete; label: string }[] = [
  { key: 'profile', label: 'Profile' },
  { key: 'program', label: 'Program' },
  { key: 'data', label: 'Data' },
  { key: 'team', label: 'Invite team' },
]

// Spec 30 §8 — progress rail uses --secondary (cobalt). No gold here; gold is
// reserved for the single completion moment on Finish.
export default function ProgressRail({
  current,
  stepsComplete,
}: {
  current: number // 1..4
  stepsComplete: SetupStepsComplete
}) {
  return (
    <ol className="flex items-center" aria-label="Setup progress">
      {SETUP_STEPS.map((step, i) => {
        const num = i + 1
        const done = stepsComplete[step.key]
        const isCurrent = num === current
        return (
          <li key={step.key} className="flex items-center" aria-current={isCurrent ? 'step' : undefined}>
            <div className="flex flex-col items-center gap-1.5">
              <span
                className={[
                  'flex h-9 w-9 items-center justify-center rounded-full text-sm font-semibold transition-colors',
                  done
                    ? 'bg-secondary text-secondary-foreground'
                    : isCurrent
                      ? 'bg-secondary/10 text-secondary ring-2 ring-secondary'
                      : 'bg-muted text-muted-foreground',
                ].join(' ')}
              >
                {done && !isCurrent ? <Check size={16} strokeWidth={2.5} /> : num}
              </span>
              <span
                className={[
                  'text-[11px] font-medium sm:text-xs',
                  isCurrent ? 'text-foreground' : 'text-muted-foreground',
                ].join(' ')}
              >
                {step.label}
              </span>
            </div>
            {i < SETUP_STEPS.length - 1 && (
              <span
                className={[
                  'mx-2 mb-5 h-0.5 w-6 rounded-full transition-colors sm:w-12',
                  done ? 'bg-secondary' : 'bg-border',
                ].join(' ')}
              />
            )}
          </li>
        )
      })}
    </ol>
  )
}
