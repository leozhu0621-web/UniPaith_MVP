import { useEffect, useState } from 'react'
import { prefersReducedMotion } from '../../hooks/useCountUp'

/**
 * Ship B (platform UX overhaul §2) — overlay presence for exit animations.
 *
 * CSS alone can animate an element IN, but anything conditionally rendered
 * unmounts instantly on close. `usePresence` keeps the element mounted for
 * `durMs` after `open` flips false so an exit animation can play:
 *
 *   const { mounted, closing } = usePresence(isOpen)
 *   if (!mounted) return null
 *   <div className={closing ? 'animate-scale-out' : 'animate-scale-in'} />
 *
 * `closing` is derived (mounted && !open), so it is true for exactly the exit
 * window. Reduced motion (OS media query OR the in-app toggle) collapses the
 * hold to 0 — this is a JS timer, so the global CSS gates in index.css can't
 * cover it. Reopening mid-exit cancels the pending unmount (effect cleanup),
 * as does unmounting the owner.
 */
export function usePresence(open: boolean, durMs = 200): { mounted: boolean; closing: boolean } {
  const [mounted, setMounted] = useState(open)

  useEffect(() => {
    if (open) {
      setMounted(true)
      return
    }
    const delay = prefersReducedMotion() ? 0 : durMs
    const timer = setTimeout(() => setMounted(false), delay)
    return () => clearTimeout(timer)
  }, [open, durMs])

  return { mounted, closing: mounted && !open }
}
