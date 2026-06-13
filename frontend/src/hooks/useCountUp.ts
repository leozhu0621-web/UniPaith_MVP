import { useEffect, useRef, useState } from 'react'

/**
 * Ship B (platform UX overhaul §2) — Imprint-style animated numerals.
 *
 * True when the user asked for reduced motion, via EITHER the OS media query
 * or the in-app Settings toggle (`html[data-reduce-motion]`, theme-store).
 * JS-driven motion (rAF counters, hold timers) must check this explicitly —
 * the global CSS gates in index.css only neutralize CSS animation/transition.
 * SSR-safe: with no window/document we report "reduced" so values render final.
 */
export function prefersReducedMotion(): boolean {
  if (typeof window === 'undefined' || typeof document === 'undefined') return true
  if (document.documentElement.hasAttribute('data-reduce-motion')) return true
  return window.matchMedia?.('(prefers-reduced-motion: reduce)').matches ?? false
}

/**
 * rAF-driven ease-out count-up: 0 → value on mount, previous → value on
 * change (~600ms, cubic ease-out to match --ease-out's settle). Intermediate
 * frames round to integers; the final frame lands on the exact value, so
 * decimal inputs (3.6 GPA) still display precisely at rest.
 *
 * Reduced motion → returns the value instantly, no timer. Re-renders with the
 * SAME value never replay (the effect keys on the value itself).
 */
export function useCountUp(value: number, opts?: { durMs?: number }): number {
  const durMs = opts?.durMs ?? 600
  const [display, setDisplay] = useState(() => (prefersReducedMotion() ? value : 0))
  // Latest displayed value — the start point when `value` changes mid-flight.
  const displayRef = useRef(display)

  useEffect(() => {
    if (prefersReducedMotion()) {
      displayRef.current = value
      setDisplay(value)
      return
    }
    const from = displayRef.current
    if (from === value) return
    const start = performance.now()
    let raf = requestAnimationFrame(function tick(now: number) {
      const t = durMs <= 0 ? 1 : Math.min(1, (now - start) / durMs)
      const eased = 1 - Math.pow(1 - t, 3)
      const next = t >= 1 ? value : Math.round(from + (value - from) * eased)
      displayRef.current = next
      setDisplay(next)
      if (t < 1) raf = requestAnimationFrame(tick)
    })
    return () => cancelAnimationFrame(raf)
  }, [value, durMs])

  return display
}
