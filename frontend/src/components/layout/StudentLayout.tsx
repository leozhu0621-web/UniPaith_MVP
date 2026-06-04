import { useState } from 'react'
import SkipLink from './SkipLink'
import { Outlet, NavLink, useNavigate, useLocation, useSearchParams } from 'react-router-dom'
import { useAuthStore } from '../../stores/auth-store'
import { useCounselorStore } from '../../stores/counselor-store'
import MiniCounselorPanel from '../student/MiniCounselorPanel'
import {
  Compass, Target, FolderKanban, Newspaper,
  LogOut, User, Bookmark, Settings, MessageSquare,
} from 'lucide-react'
import Avatar from '../ui/Avatar'
import Dropdown from '../ui/Dropdown'
import NotificationBell from '../notifications/NotificationBell'
import Wordmark from '../ui/Wordmark'
import Sheet from '../ui/Sheet'
import CompareTray from '../student/CompareTray'
import TrialBanner from '../student/TrialBanner'
import Paywall from '../student/Paywall'
import { SearchTrigger, CommandPalette } from '../student/GlobalSearch'

// Stage-ordered navigation (Spec/02 §7): Discover · Match · Apply · Connect.
const NAV_ITEMS = [
  { to: '/s', icon: Compass, label: 'Discover', end: true },
  { to: '/s/explore', icon: Target, label: 'Match', end: false },
  { to: '/s/manage', icon: FolderKanban, label: 'Apply', end: false },
  { to: '/s/posts', icon: Newspaper, label: 'Connect', end: false },
]

export default function StudentLayout() {
  const { user, logout } = useAuthStore()
  const navigate = useNavigate()
  const location = useLocation()
  const [searchParams] = useSearchParams()
  const { isMinimized, setMinimized } = useCounselorStore()
  const [accountSheetOpen, setAccountSheetOpen] = useState(false)

  const isDiscoverTab = location.pathname === '/s' || location.pathname === '/s/'
  const isOtherTab = !isDiscoverTab
  const showMiniCounselor = isOtherTab && !isMinimized

  const accountItems = [
    { label: 'My Profile', to: '/s/profile', icon: <User size={16} /> },
    { label: 'Saved', to: '/s/saved', icon: <Bookmark size={16} /> },
    { label: 'Settings', to: '/s/settings', icon: <Settings size={16} /> },
  ]

  return (
    <div className="flex flex-col h-screen bg-background">
      <SkipLink />
      {/* ─── Desktop top nav (lg+) — Spec/02 §7. 64px, --bg, --border hairline. ─── */}
      <header className="hidden lg:flex h-16 items-center justify-between px-8 bg-background border-b border-border flex-shrink-0 z-30">
        <div className="flex items-center gap-4">
          <NavLink to="/s" className="leading-none" aria-label="UniPaith home">
            <Wordmark className="h-7 w-auto" />
          </NavLink>
          <SearchTrigger variant="bar" />
        </div>

        <nav className="flex items-center gap-1" aria-label="Primary">
          {NAV_ITEMS.map((item, i) => (
            <div key={item.to} className="flex items-center">
              <NavLink
                to={item.to}
                end={item.end}
                className={({ isActive }) =>
                  `ui-btn relative px-4 h-16 inline-flex items-center text-sm transition-colors ${
                    isActive ? 'text-foreground font-semibold' : 'text-muted-foreground hover:text-foreground font-medium'
                  }`
                }
              >
                {({ isActive }) => (
                  <>
                    {item.label}
                    {isActive && <span className="absolute bottom-0 left-3 right-3 h-0.5 bg-primary rounded-full" />}
                  </>
                )}
              </NavLink>
              {i === 0 && <span className="w-px h-6 bg-border mx-2" />}
            </div>
          ))}
        </nav>

        <div className="flex items-center gap-2">
          <NotificationBell />
          <Dropdown
            trigger={
              <button aria-label="Account menu" className="ui-btn p-1 rounded-lg hover:bg-muted transition-colors">
                <Avatar name={user?.email || '?'} size="sm" />
              </button>
            }
            items={[
              { label: 'My Profile', onClick: () => navigate('/s/profile'), icon: <User size={14} /> },
              { label: 'Saved', onClick: () => navigate('/s/saved'), icon: <Bookmark size={14} /> },
              { label: 'Settings', onClick: () => navigate('/s/settings'), icon: <Settings size={14} /> },
              { label: 'Sign out', onClick: logout, icon: <LogOut size={14} />, variant: 'danger' },
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
          <NotificationBell />
        </div>
      </header>

      {/* Trial / plan nudge (Spec 05 §9, 07 §4.1) */}
      <TrialBanner />

      {/* Body with sliding panels */}
      <div className="flex-1 flex overflow-hidden relative">
        {/* Mini counselor — docked on lg+ only; on mobile, Discover tab is the chat. */}
        <div
          className={`hidden lg:block flex-shrink-0 overflow-hidden transition-all duration-300 ease-in-out ${
            showMiniCounselor ? 'w-72 opacity-100' : 'w-0 opacity-0'
          }`}
        >
          <div className="w-72 h-full">
            <MiniCounselorPanel />
          </div>
        </div>

        {isOtherTab && isMinimized && (
          <button
            onClick={() => setMinimized(false)}
            className="hidden lg:flex absolute left-0 top-3 z-20 items-center gap-1 pl-1.5 pr-3 py-2 bg-card border border-border border-l-0 rounded-r-xl elev-subtle text-secondary hover:bg-muted transition-all duration-200 animate-slide-in-left"
            title="Show counselor"
          >
            <MessageSquare size={14} />
            <span className="text-[10px] font-medium">Chat</span>
          </button>
        )}

        {/* Main content — bottom padding on mobile to clear the tab bar. */}
        <main
          id="main"
          tabIndex={-1}
          className={`flex min-h-0 flex-1 flex-col outline-none transition-all duration-300 ease-in-out ${
            location.pathname.startsWith('/s/manage') ? 'overflow-hidden' : 'overflow-y-auto'
          }`}
        >
          <div
            key={location.pathname}
            className={`animate-page-in flex min-h-0 flex-1 flex-col pb-[calc(64px+env(safe-area-inset-bottom))] lg:pb-0 ${
              location.pathname.startsWith('/s/manage') ? '' : 'min-h-full'
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
            className={({ isActive }) =>
              `touch-target flex-1 flex flex-col items-center justify-center gap-0.5 ${
                isActive ? 'text-secondary' : 'text-muted-foreground'
              }`
            }
          >
            <item.icon size={20} strokeWidth={1.75} />
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

      {/* Global ⌘K command palette — search programs/schools + jump to any surface. */}
      <CommandPalette />

      {/* Trial→paywall gate (Spec 05 §9) — only blocks when enforced + lapsed. */}
      <Paywall />
    </div>
  )
}
