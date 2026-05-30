// StudentLayout — Spec/02 §7 (top nav) + Spec/02b §3.1 (bottom tab bar
// on base–md). Desktop: top nav with 4 stage labels + avatar dropdown.
// Mobile: top bar w/ wordmark + bell only; primary nav becomes a fixed
// bottom tab bar.

import { Outlet, NavLink, useNavigate, useLocation } from 'react-router-dom'
import clsx from 'clsx'
import { useAuthStore } from '../../stores/auth-store'
import { useCounselorStore } from '../../stores/counselor-store'
import MiniCounselorPanel from '../student/MiniCounselorPanel'
import {
  Compass, Target, FolderKanban, Newspaper,
  Bell, LogOut, User, Bookmark, Settings, MessageSquare,
} from 'lucide-react'
import Avatar from '../ui/Avatar'
import Dropdown from '../ui/Dropdown'
import Wordmark from '../ui/Wordmark'
import CompareTray from '../student/CompareTray'
import StudentBottomNav from '../student/StudentBottomNav'

const TOP_NAV = [
  { to: '/s', icon: Compass, label: 'Discover', end: true },
  { to: '/s/explore', icon: Target, label: 'Match' },
  { to: '/s/manage', icon: FolderKanban, label: 'Apply' },
  { to: '/s/posts', icon: Newspaper, label: 'Connect' },
] as const

export default function StudentLayout() {
  const { user, logout } = useAuthStore()
  const navigate = useNavigate()
  const location = useLocation()
  const { isMinimized, setMinimized } = useCounselorStore()

  const isDiscoverTab = location.pathname === '/s' || location.pathname === '/s/'
  const isOtherTab = !isDiscoverTab
  const showMiniCounselor = isOtherTab && !isMinimized

  return (
    <div className="flex flex-col h-screen bg-background">
      {/* Top bar — full chrome on desktop; compact wordmark on mobile. */}
      <header className="h-16 flex items-center justify-between px-4 lg:px-6 bg-card border-b border-border flex-shrink-0 z-30">
        <NavLink to="/s" className="leading-none" aria-label="UniPaith home">
          <Wordmark className="h-7 w-auto" />
        </NavLink>

        {/* Desktop nav — 4 stages, gold underline on active. */}
        <nav className="hidden lg:flex items-center" aria-label="Primary">
          <NavLink
            to="/s"
            end
            className={({ isActive }) =>
              clsx(
                'flex flex-col items-center px-4 py-1.5 rounded-lg motion-fast transition-colors relative',
                isActive ? 'text-foreground' : 'text-muted-foreground hover:text-foreground',
              )
            }
          >
            {({ isActive }) => (
              <>
                <Compass size={19} aria-hidden />
                <span className="text-[10px] mt-0.5 font-bold">Discover</span>
                {isActive && (
                  <span className="absolute -bottom-px left-2 right-2 h-0.5 bg-[#FFD60A] dark:bg-[#F2C800] rounded-full" />
                )}
              </>
            )}
          </NavLink>

          <div className="w-px h-8 bg-border mx-1" aria-hidden="true" />

          {TOP_NAV.slice(1).map(item => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                clsx(
                  'flex flex-col items-center px-4 py-1.5 rounded-lg motion-fast transition-colors relative',
                  isActive ? 'text-foreground' : 'text-muted-foreground hover:text-foreground',
                )
              }
            >
              {({ isActive }) => (
                <>
                  <item.icon size={19} aria-hidden />
                  <span className="text-[10px] mt-0.5 font-bold">{item.label}</span>
                  {isActive && (
                    <span className="absolute -bottom-px left-2 right-2 h-0.5 bg-[#FFD60A] dark:bg-[#F2C800] rounded-full" />
                  )}
                </>
              )}
            </NavLink>
          ))}
        </nav>

        <div className="flex items-center gap-1.5">
          <button
            onClick={() => navigate('/s/manage?tab=messages')}
            aria-label="Open messages"
            className="relative p-2 rounded-lg hover:bg-muted text-muted-foreground hover:text-foreground motion-fast transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#FFD60A]"
          >
            <Bell size={19} />
          </button>

          {/* Avatar dropdown — desktop only (mobile has the account sheet). */}
          <div className="hidden lg:block">
            <Dropdown
              trigger={
                <button className="p-1 rounded-lg hover:bg-muted motion-fast transition-colors">
                  <Avatar name={user?.email || '?'} size="sm" />
                </button>
              }
              items={[
                { label: 'My profile', onClick: () => navigate('/s/profile'), icon: <User size={14} /> },
                { label: 'Saved', onClick: () => navigate('/s/saved'), icon: <Bookmark size={14} /> },
                { label: 'Settings', onClick: () => navigate('/s/settings'), icon: <Settings size={14} /> },
                { label: 'Sign out', onClick: logout, icon: <LogOut size={14} />, variant: 'danger' },
              ]}
            />
          </div>
        </div>
      </header>

      {/* Body with sliding panels */}
      <div className="flex-1 flex overflow-hidden relative">
        {/* Mini counselor panel — desktop only; collapses on mobile. */}
        <div
          className={clsx(
            'hidden lg:block flex-shrink-0 overflow-hidden motion-base transition-all',
            showMiniCounselor ? 'w-72 opacity-100' : 'w-0 opacity-0',
          )}
        >
          <div className="w-72 h-full">
            <MiniCounselorPanel />
          </div>
        </div>

        {/* Show counselor toggle button when minimized — desktop only. */}
        {isOtherTab && isMinimized && (
          <button
            onClick={() => setMinimized(false)}
            className="hidden lg:flex absolute left-0 top-3 z-20 items-center gap-1 pl-1.5 pr-3 py-2 bg-card border border-border border-l-0 rounded-r-xl elev-subtle text-foreground hover:bg-muted motion-fast transition-all animate-slide-in-left"
            title="Show counselor"
          >
            <MessageSquare size={14} />
            <span className="text-[10px] font-bold">Chat</span>
          </button>
        )}

        {/* Main content area with page transition. Leaves room for the
            mobile bottom tab bar (h-14 + safe area) below lg. */}
        <main className="flex-1 overflow-y-auto motion-base transition-all pb-14 lg:pb-0">
          <div key={location.pathname} className="animate-page-in h-full">
            <Outlet />
          </div>
        </main>
      </div>

      {/* Mobile bottom tab bar — hidden ≥lg. */}
      <StudentBottomNav />

      <CompareTray />
    </div>
  )
}
