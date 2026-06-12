import { useState } from 'react'
import SkipLink from './SkipLink'
import { Outlet, NavLink, useNavigate, useLocation, useSearchParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { useAuthStore } from '../../stores/auth-store'
import {
  Compass, Target, Backpack,
  LogOut, Settings, Inbox, WifiOff,
} from 'lucide-react'
import { getUnseenCount } from '../../api/connect'
import { getConnectSeenAt } from '../../utils/connectSeen'
import { MY_SPACE_ROUTES } from '../../pages/student/myspace/MySpaceShell'
import Avatar from '../ui/Avatar'
import Dropdown from '../ui/Dropdown'
import NotificationBell from '../notifications/NotificationBell'
import Sheet from '../ui/Sheet'
import CompareTray from '../student/CompareTray'
import TrialBanner from '../student/TrialBanner'
import Paywall from '../student/Paywall'
import { SearchTrigger, CommandPalette } from '../student/GlobalSearch'
import ScrollReset from './ScrollReset'
import StudentTitle from './StudentTitle'
import MessagesNavButton from '../student/MessagesNavButton'
import LiveAnnouncer from '../a11y/LiveAnnouncer'
import { useOnlineStatus } from '../../hooks/useOnlineStatus'
import { COPY } from '../../lib/copy'

// Journey-ordered navigation (Spec 2026-06-12): Uni · Discover · My Space —
// Connect merged into the Discover hub (updates/events/peers tabs + live
// rail), so the nav is two surfaces about the world + one about you, next to
// the avatar. My Space owns every room route, so its active state is
// computed from the location rather than NavLink's single-path match.
const NAV_ITEMS = [
  { to: '/s', icon: Compass, label: 'Uni', end: true },
  { to: '/s/explore', icon: Target, label: 'Discover', end: false },
  { to: '/s/space', icon: Backpack, label: 'My Space', end: false },
]

const isMySpacePath = (pathname: string) =>
  MY_SPACE_ROUTES.some(p => pathname === p || pathname.startsWith(`${p}/`))

export default function StudentLayout() {
  const { user, logout } = useAuthStore()
  const navigate = useNavigate()
  const location = useLocation()
  const [searchParams] = useSearchParams()
  const [accountSheetOpen, setAccountSheetOpen] = useState(false)
  const online = useOnlineStatus()

  // "New updates" dot on Discover (Spec 2026-06-12 §6.3) — posts since the
  // student last opened the Updates tab; the tab itself clears it.
  const { data: unseenCount = 0 } = useQuery({
    queryKey: ['connect-unseen'],
    queryFn: () => getUnseenCount(getConnectSeenAt()),
    staleTime: 5 * 60 * 1000,
    retry: false,
  })

  // Spec 2026-06-10 §1 — Profile and Saved live in the My Space rail now;
  // the account menu keeps only account-level items.
  const accountItems = [
    { label: 'Settings', to: '/s/settings', icon: <Settings size={16} /> },
    // Owner-only: in-app feedback inbox (gated server-side by the email allowlist).
    ...(user?.is_owner
      ? [{ label: 'Feedback inbox', to: '/s/feedback', icon: <Inbox size={16} /> }]
      : []),
  ]

  return (
    <div className="flex flex-col h-dvh bg-background">
      <SkipLink />
      {/* ─── Desktop top nav (lg+) — Spec/02 §7. 64px, --bg, --border hairline. ─── */}
      <header className="hidden lg:flex h-16 items-center justify-between px-8 bg-background border-b border-border flex-shrink-0 z-30">
        <div className="flex flex-1 items-center gap-3">
          <NavLink to="/s" className="leading-none" aria-label="UniPaith home">
            <img src="/favicon.svg" alt="UniPaith" className="h-9 w-9 rounded-md" />
          </NavLink>
          <SearchTrigger variant="icon" />
        </div>

        <nav className="flex items-center gap-1" aria-label="Primary">
          {NAV_ITEMS.map((item, i) => (
            <div key={item.to} className="flex items-center">
              <NavLink
                to={item.to}
                end={item.end}
                className={({ isActive }) => {
                  const active = item.to === '/s/space' ? isMySpacePath(location.pathname) : isActive
                  return `ui-btn relative px-4 h-16 inline-flex items-center text-sm transition-colors ${
                    active ? 'text-foreground font-semibold' : 'text-muted-foreground hover:text-foreground font-medium'
                  }`
                }}
              >
                {({ isActive }) => {
                  const active = item.to === '/s/space' ? isMySpacePath(location.pathname) : isActive
                  return (
                    <>
                      {item.label}
                      {item.to === '/s/explore' && unseenCount > 0 && (
                        <span className="absolute top-4 right-1 w-1.5 h-1.5 rounded-full bg-secondary" aria-hidden="true" />
                      )}
                      {active && <span className="absolute bottom-0 left-3 right-3 h-0.5 bg-secondary rounded-full" />}
                    </>
                  )
                }}
              </NavLink>
              {i === 0 && <span className="w-px h-6 bg-border mx-2" />}
            </div>
          ))}
        </nav>

        <div className="flex flex-1 items-center justify-end gap-2">
          <MessagesNavButton />
          <NotificationBell />
          <Dropdown
            trigger={
              <button aria-label="Account menu" className="ui-btn p-1 rounded-lg hover:bg-muted transition-colors">
                <Avatar name={user?.email || '?'} size="sm" />
              </button>
            }
            items={[
              { label: 'Settings', onClick: () => navigate('/s/settings'), icon: <Settings size={14} /> },
              ...(user?.is_owner
                ? [{ label: 'Feedback inbox', onClick: () => navigate('/s/feedback'), icon: <Inbox size={14} /> }]
                : []),
              { label: 'Sign out', onClick: logout, icon: <LogOut size={14} />, variant: 'danger' as const },
            ]}
          />
        </div>
      </header>

      {/* ─── Mobile top bar (< lg) — monogram + notifications (Spec/02b §10). ─── */}
      <header className="flex lg:hidden h-14 items-center justify-between px-4 bg-background border-b border-border flex-shrink-0 z-30">
        <NavLink to="/s" aria-label="UniPaith home" className="leading-none">
          <img src="/favicon.svg" alt="UniPaith" className="h-9 w-9 rounded-md" />
        </NavLink>
        <div className="flex items-center gap-1">
          <SearchTrigger variant="icon" />
          <MessagesNavButton />
          <NotificationBell />
        </div>
      </header>

      {/* Offline banner (Spec 78 §5) — app-wide, auto-clears on reconnect. */}
      {!online && (
        <div
          role="status"
          className="flex items-center gap-2 px-4 sm:px-8 py-2 border-b border-warning/40 bg-warning-soft text-sm text-foreground"
        >
          <WifiOff size={15} className="text-warning shrink-0" />
          <span className="flex-1 min-w-0 truncate">{COPY.offline}</span>
        </div>
      )}

      {/* Trial / plan nudge (Spec 05 §9, 07 §4.1) */}
      <TrialBanner />

      {/* Body */}
      <div className="flex-1 flex overflow-hidden">
        {/* Main content — bottom padding on mobile to clear the tab bar. */}
        {/* overflow-x-clip + min-w-0 — a too-wide child can no longer pan the
            whole shell horizontally (UX overhaul Ship A, 2026-06-12 spec §1).
            The wrapper below is intentionally NOT keyed by pathname: the shell
            persists across navigations; page-entrance motion lives in
            PageContainer / detail-page roots instead. */}
        <main
          id="main"
          tabIndex={-1}
          className={`flex min-h-0 min-w-0 flex-1 flex-col overflow-x-clip outline-none transition-all duration-300 ease-in-out ${
            location.pathname.startsWith('/s/messages') ? 'overflow-hidden' : 'overflow-y-auto'
          }`}
        >
          <div
            className={`flex min-h-0 flex-1 flex-col pb-[calc(64px+env(safe-area-inset-bottom))] lg:pb-0 ${
              location.pathname.startsWith('/s/messages') ? '' : 'min-h-full'
            }`}
          >
            <Outlet />
          </div>
        </main>
      </div>

      {/* ─── Mobile bottom tab bar (< lg) — Spec/02b §3.1. 56px, cobalt active. ─── */}
      <nav
        className="flex lg:hidden fixed bottom-0 inset-x-0 z-40 h-[calc(56px+env(safe-area-inset-bottom))] pb-safe bg-background border-t border-border"
        aria-label="Primary"
      >
        {NAV_ITEMS.map(item => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.end}
            className={({ isActive }) => {
              const active = item.to === '/s/space' ? isMySpacePath(location.pathname) : isActive
              return `touch-target flex-1 flex flex-col items-center justify-center gap-0.5 ${
                active ? 'text-secondary' : 'text-muted-foreground'
              }`
            }}
          >
            <span className="relative">
              <item.icon size={20} strokeWidth={1.75} />
              {item.to === '/s/explore' && unseenCount > 0 && (
                <span className="absolute -top-0.5 -right-1 w-1.5 h-1.5 rounded-full bg-secondary" aria-hidden="true" />
              )}
            </span>
            <span className="text-[10px] font-semibold">{item.label}</span>
          </NavLink>
        ))}
        <button
          onClick={() => setAccountSheetOpen(true)}
          className="touch-target flex-1 flex flex-col items-center justify-center gap-0.5 text-muted-foreground"
          aria-label="Account"
        >
          <Avatar name={user?.email || '?'} size="sm" className="!w-5 !h-5 !text-[9px]" />
          <span className="text-[10px] font-semibold">Account</span>
        </button>
      </nav>

      {/* Account sheet (mobile) — Profile · Saved · Settings · Sign out. */}
      <Sheet isOpen={accountSheetOpen} onClose={() => setAccountSheetOpen(false)} side="bottom" title="Account">
        <div className="flex items-center gap-3 pb-3 mb-1 border-b border-border">
          <Avatar name={user?.email || '?'} size="md" />
          <span className="text-sm text-foreground truncate">{user?.email}</span>
        </div>
        <div className="flex flex-col">
          {accountItems.map(item => (
            <button
              key={item.to}
              onClick={() => { setAccountSheetOpen(false); navigate(item.to) }}
              className="touch-target flex items-center gap-3 px-1 py-3 text-sm text-foreground hover:bg-muted rounded-md transition-colors"
            >
              <span className="text-muted-foreground">{item.icon}</span>
              {item.label}
            </button>
          ))}
          <button
            onClick={() => { setAccountSheetOpen(false); logout() }}
            className="touch-target flex items-center gap-3 px-1 py-3 text-sm text-error hover:bg-error-soft/50 rounded-md transition-colors"
          >
            <LogOut size={16} /> Sign out
          </button>
        </div>
      </Sheet>

      <CompareTray
        initialExpanded={location.pathname === '/s/explore' && searchParams.get('compare') === 'open'}
        syncUrl={location.pathname === '/s/explore'}
      />

      {/* Scroll policy (the <main> scroll container persists across routes):
          restore position on back/forward, reset to top on push — and always
          clear any horizontal pan. */}
      <ScrollReset />
      <StudentTitle />

      {/* Global ⌘K command palette — search programs/schools + jump to any surface. */}
      <CommandPalette />

      {/* Trial→paywall gate (Spec 05 §9) — only blocks when enforced + lapsed. */}
      <Paywall />

      {/* App-wide polite ARIA live region (Spec 80 §4) — optimistic-action announcements. */}
      <LiveAnnouncer />
    </div>
  )
}
