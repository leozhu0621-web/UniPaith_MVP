import { useEffect, type ReactNode } from 'react'
import clsx from 'clsx'
import { useCoachmarkStore } from '../../stores/coachmark-store'

interface CoachmarkProps {
  /** Stable unique id — also the localStorage dismissal key. */
  id: string
  title: string
  body: string
  /** Where the bubble sits relative to the wrapped anchor. */
  placement?: 'top' | 'bottom' | 'left' | 'right'
  children: ReactNode
  className?: string
}

const POS: Record<NonNullable<CoachmarkProps['placement']>, string> = {
  bottom: 'top-full left-1/2 -translate-x-1/2 mt-2',
  top: 'bottom-full left-1/2 -translate-x-1/2 mb-2',
  right: 'left-full top-1/2 -translate-y-1/2 ml-2',
  left: 'right-full top-1/2 -translate-y-1/2 mr-2',
}

/**
 * First-run coachmark (Spec 81 §3.3). Wrap a signature element; the first time
 * it mounts (and no earlier-registered coachmark is pending) a small cobalt
 * bubble explains it. Dismissal is one-time + persisted. Cobalt accent — never
 * gold (this is orientation chrome, not an earned beat).
 */
export default function Coachmark({
  id,
  title,
  body,
  placement = 'bottom',
  children,
  className,
}: CoachmarkProps) {
  const register = useCoachmarkStore((s) => s.register)
  const unregister = useCoachmarkStore((s) => s.unregister)
  const dismiss = useCoachmarkStore((s) => s.dismiss)
  const activeId = useCoachmarkStore((s) => s.activeId)
  const seen = useCoachmarkStore((s) => s.seen)

  useEffect(() => {
    register(id)
    return () => unregister(id)
  }, [id, register, unregister])

  const show = activeId === id && !seen[id]

  return (
    <div className={clsx('relative', className)}>
      {children}
      {show && (
        <div
          role="dialog"
          aria-label={title}
          className={clsx(
            'absolute z-50 w-56 rounded-lg border border-secondary/40 bg-card p-3 text-left elev-raised motion-safe:animate-page-in',
            POS[placement],
          )}
        >
          <p className="text-xs font-semibold text-foreground">{title}</p>
          <p className="mt-1 text-xs leading-relaxed text-muted-foreground">{body}</p>
          <button
            onClick={() => dismiss(id)}
            className="ui-btn mt-2 text-xs font-semibold text-secondary hover:underline"
          >
            Got it
          </button>
        </div>
      )}
    </div>
  )
}
