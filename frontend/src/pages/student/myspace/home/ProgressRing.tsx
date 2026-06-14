// Gold progress ring — mounts empty, then a double rAF flips `drawn` so the
// 0.8s dashoffset transition plays the initial fill (DualRing's pattern).
// Reduced motion mounts pre-drawn; the numeral counts up alongside.
// (UX overhaul Ship C §3; extracted for reuse by the My Space momentum band.)
import { useEffect, useState } from 'react'
import { prefersReducedMotion, useCountUp } from '../../../../hooks/useCountUp'

export default function ProgressRing({ pct, size = 64, stroke = 6 }: { pct: number; size?: number; stroke?: number }) {
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
