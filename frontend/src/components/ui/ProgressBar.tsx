import clsx from 'clsx'
import { useEffect, useState } from 'react'

import { prefersReducedMotion } from '../../hooks/useCountUp'

interface ProgressBarProps {
  value: number // 0-100
  label?: string
  className?: string
}

export default function ProgressBar({ value, label, className }: ProgressBarProps) {
  const clamped = Math.max(0, Math.min(100, value))

  // Ship B motion: mount at 0 width, then a double rAF flips `drawn` so the
  // existing width transition animates the initial fill (Imprint progress
  // language). Later value changes animate via the same transition; reduced
  // motion mounts pre-drawn. The aria value always reports the real number.
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
    <div className={clsx('w-full', className)}>
      {label && (
        <div className="flex justify-between mb-1">
          <span className="text-xs text-muted-foreground">{label}</span>
          <span className="text-xs text-muted-foreground tabular-nums">{Math.round(clamped)}%</span>
        </div>
      )}
      <div
        className="w-full bg-muted rounded-pill h-2 overflow-hidden"
        role="progressbar"
        aria-valuenow={Math.round(clamped)}
        aria-valuemin={0}
        aria-valuemax={100}
      >
        <div
          className="bg-secondary h-2 rounded-pill transition-all duration-300"
          style={{ width: `${drawn ? clamped : 0}%` }}
        />
      </div>
    </div>
  )
}
