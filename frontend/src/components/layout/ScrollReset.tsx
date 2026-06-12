import { useEffect } from 'react'
import { useLocation, useNavigationType } from 'react-router-dom'

// One scroll/navigation policy (UX overhaul Ship A, 2026-06-12 spec §1). The
// `<main id="main">` scroll container persists across navigations, so:
//
//   - PUSH / REPLACE (including `?tab=` switches) → scroll to top.
//   - POP (back/forward) → restore the position saved for that history entry
//     (sessionStorage, keyed by `location.key`). Lazy route chunks mean the
//     content may mount async under Suspense, so the restore retries over a
//     few animation frames (~400ms) until the container can accommodate it.
//   - ALWAYS clear horizontal scroll — a transient too-wide child must never
//     leave the shell panned sideways on the next page.
//
// Positions are recorded from a passive scroll listener (keyed by the current
// location) rather than on unmount, because by cleanup time the next page has
// already swapped in and the browser may have clamped scrollTop.
// Skips when there's a hash so in-page anchor links still scroll to their
// target. Mount once near the layout root.

const STORAGE_PREFIX = 'up-scroll:'

function saveScroll(key: string, top: number) {
  try {
    sessionStorage.setItem(`${STORAGE_PREFIX}${key}`, String(top))
  } catch {
    // Storage full/unavailable — restoration is best-effort.
  }
}

function readScroll(key: string): number | null {
  try {
    const raw = sessionStorage.getItem(`${STORAGE_PREFIX}${key}`)
    if (raw == null) return null
    const top = Number(raw)
    return Number.isFinite(top) ? top : null
  } catch {
    return null
  }
}

export default function ScrollReset() {
  const location = useLocation()
  const navigationType = useNavigationType()
  const { key, pathname, search, hash } = location

  // Record this entry's scroll position as the user scrolls, so the latest
  // value is already persisted by the time a navigation swaps the page out.
  useEffect(() => {
    const main = document.getElementById('main')
    if (!main) return
    const onScroll = () => saveScroll(key, main.scrollTop)
    main.addEventListener('scroll', onScroll, { passive: true })
    return () => main.removeEventListener('scroll', onScroll)
  }, [key])

  // Apply the policy whenever the route (pathname or search) changes.
  useEffect(() => {
    if (hash) return // in-page anchor — let the browser handle it
    const main = document.getElementById('main')
    if (!main) {
      window.scrollTo(0, 0)
      return
    }

    const saved = navigationType === 'POP' ? readScroll(key) : null
    if (saved == null || saved <= 0) {
      main.scrollTo({ top: 0, left: 0 })
      return
    }

    // POP with a saved position: the page chunk/content may still be mounting
    // under Suspense, so retry until the container is tall enough (or ~400ms
    // passes), then apply best-effort and stop.
    let rafId = 0
    const deadline = Date.now() + 400
    const tryRestore = () => {
      const canFit = main.scrollHeight - main.clientHeight >= saved
      if (canFit || Date.now() >= deadline) {
        main.scrollTo({ top: saved, left: 0 })
        return
      }
      rafId = requestAnimationFrame(tryRestore)
    }
    tryRestore()
    return () => cancelAnimationFrame(rafId)
  }, [key, pathname, search, hash, navigationType])

  return null
}
