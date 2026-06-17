import clsx from 'clsx'
import { Check } from 'lucide-react'

export interface StepperStep {
  key: string
  label: string
}

interface StepperProps {
  steps: StepperStep[]
  /** The step the journey is currently on. Earlier steps render as done. */
  currentKey: string
  className?: string
}

/** A flat horizontal stepper — turns a linear status into something the eye can
 *  follow. Done steps fill cobalt with a check, the current step rings cobalt,
 *  future steps stay muted outline; connectors are cobalt up to the current
 *  step and muted after. Display only — no actions, token-colored, static (no
 *  motion to reduce). The list reports order and marks the current step with
 *  `aria-current` for assistive tech. */
export default function Stepper({ steps, currentKey, className }: StepperProps) {
  const currentIndex = Math.max(
    0,
    steps.findIndex(s => s.key === currentKey)
  )

  return (
    <ol className={clsx('flex items-start w-full', className)}>
      {steps.map((step, i) => {
        const done = i < currentIndex
        const current = i === currentIndex
        const connectorDone = i <= currentIndex
        return (
          <li
            key={step.key}
            className="flex flex-col items-center flex-1 min-w-0"
            aria-current={current ? 'step' : undefined}
          >
            <div className="flex items-center w-full">
              {/* left connector — hidden on the first node */}
              <span
                className={clsx(
                  'h-0.5 flex-1 rounded-pill',
                  i === 0 ? 'invisible' : done || current ? 'bg-secondary' : 'bg-muted'
                )}
                aria-hidden="true"
              />
              <span
                className={clsx(
                  'shrink-0 w-6 h-6 rounded-full flex items-center justify-center text-xs font-semibold',
                  done && 'bg-secondary text-white',
                  current && 'bg-secondary/10 text-secondary ring-2 ring-secondary',
                  !done && !current && 'bg-card text-muted-foreground ring-1 ring-border'
                )}
              >
                {done ? <Check size={14} aria-hidden="true" /> : i + 1}
              </span>
              {/* right connector — hidden on the last node */}
              <span
                className={clsx(
                  'h-0.5 flex-1 rounded-pill',
                  i === steps.length - 1 ? 'invisible' : connectorDone && !current ? 'bg-secondary' : 'bg-muted'
                )}
                aria-hidden="true"
              />
            </div>
            <span
              className={clsx(
                'mt-1.5 text-[11px] leading-tight text-center px-1 truncate max-w-full',
                current ? 'text-foreground font-semibold' : done ? 'text-foreground' : 'text-muted-foreground'
              )}
              title={step.label}
            >
              {step.label}
            </span>
          </li>
        )
      })}
    </ol>
  )
}
