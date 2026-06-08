import { useEffect } from 'react'
import { useLocation, useSearchParams } from 'react-router-dom'

// LinkedIn-style per-route browser tab title: "<Page> · UniPaith". Mounted once
// in StudentLayout. Only sets a title for routes it knows; dynamic detail pages
// that set their own (e.g. ApplicationDetailPage → the program name) are skipped
// here so they win. Runs as a layout (parent) effect — after child page effects —
// so for known routes it is authoritative.

const APP_SUFFIX = ' · UniPaith'

const ROUTE_TITLES: Record<string, string> = {
  '/s': 'Uni',
  '/s/explore': 'Match',
  '/s/posts': 'Connect',
  '/s/profile': 'Profile',
  '/s/saved': 'Saved',
  '/s/settings': 'Settings',
  '/s/recommendations': 'Matches',
  '/s/financial-aid': 'Financial aid',
  '/s/onboarding': 'Welcome',
  '/s/feedback': 'Feedback',
}

// Apply (/s/manage) sub-tabs — the title reflects the active tab.
const MANAGE_TABS: Record<string, string> = {
  applications: 'Applications',
  calendar: 'Calendar',
  messages: 'Messages',
  prompts: 'Prompt Library',
  workshops: 'Workshops',
}

function titleFor(pathname: string, tab: string | null): string | undefined {
  if (pathname.startsWith('/s/manage')) return MANAGE_TABS[tab ?? 'applications'] ?? 'Applications'
  if (pathname in ROUTE_TITLES) return ROUTE_TITLES[pathname]
  // Dynamic detail routes: applications set their own specific title; programs /
  // schools get a generic fallback (no per-page wiring needed, never stale).
  if (pathname.startsWith('/s/applications/')) return undefined
  if (pathname.startsWith('/s/programs/')) return 'Program'
  if (pathname.startsWith('/s/institutions/')) return 'School'
  return undefined
}

export default function StudentTitle() {
  const { pathname } = useLocation()
  const [sp] = useSearchParams()
  const tab = sp.get('tab')
  useEffect(() => {
    const name = titleFor(pathname, tab)
    if (name) document.title = name + APP_SUFFIX
  }, [pathname, tab])
  return null
}
