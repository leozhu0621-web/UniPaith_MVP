import clsx from 'clsx'
import { useEffect, useState } from 'react'

import { prefersReducedMotion } from '../../hooks/useCountUp'

interface StatBarProps {
  /** The magnitude this bar represents. */
  value: number
  /** The full-width reference (the row max). Bars in a row share one max. */
  max: number
  /** Highlight this bar as the winning column (cobalt fill vs. muted). */
  best?: boolean
  className?: string
}

/** A flat horizontal magnitude bar — turns a number into something the eye can
 *  scan. Cobalt (--secondary) when it's the winner, muted otherwise. The fill
 *  grows on mount via a width transition; reduced motion mounts pre-drawn. */
export default function StatBar({ value, max, best = false, className }: StatBarProps) {
  const pct = max > 0 ? Math.max(0, Math.min(100, (value / max) * 100)) : 0
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

  return (
    <div className={clsx('w-full bg-muted rounded-pill h-1.5 overflow-hidden', className)} aria-hidden="true">
      <div
        className={clsx(
          'h-1.5 rounded-pill transition-all duration-300',
          best ? 'bg-secondary' : 'bg-muted-foreground/40'
        )}
        style={{ width: `${drawn ? pct : 0}%` }}
      />
    </div>
  )
}
