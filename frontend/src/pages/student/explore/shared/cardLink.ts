import type { MouseEvent } from 'react'

/**
 * Click guard for card-root links (UX overhaul Ship D §4 — link semantics).
 *
 * Entity cards render a real <Link>/<a> so keyboard focus, Enter, and
 * cmd/ctrl/middle-click open-in-new-tab all work. Plain left clicks run the
 * caller's existing handler (analytics + navigate) and suppress the link's
 * own navigation so history isn't pushed twice; modified clicks fall through
 * to the browser untouched.
 */
export function cardLinkClick(onActivate: () => void) {
  return (e: MouseEvent<HTMLAnchorElement>) => {
    if (e.defaultPrevented) return
    if (e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return
    e.preventDefault()
    onActivate()
  }
}

/**
 * Stretched-link overlay for card roots (root gets `relative`): the title
 * link covers the whole card without nesting the inner action <button>s
 * inside the anchor (no nested-interactive a11y violation — raise those
 * buttons with `relative z-10` instead). Focus ring draws around the card.
 */
export const CARD_LINK_OVERLAY =
  "after:absolute after:inset-0 after:content-[''] after:rounded-lg outline-none focus-visible:after:ring-2 focus-visible:after:ring-secondary"
