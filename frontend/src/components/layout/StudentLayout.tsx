import { Outlet, NavLink, useNavigate, useLocation } from 'react-router-dom'
import { useAuthStore } from '../../stores/auth-store'
import { useCounselorStore } from '../../stores/counselor-store'
import MiniCounselorPanel from '../student/MiniCounselorPanel'
import {
  Compass, Target, FolderKanban, Newspaper,
  Bell, LogOut, User, Bookmark, Settings, MessageSquare, Menu,
} from 'lucide-react'
import Avatar from '../ui/Avatar'
import Dropdown from '../ui/Dropdown'
import Wordmark from '../ui/Wordmark'
import CompareTray from '../student/CompareTray'
import { useDocumentTitle } from '../../hooks/useDocumentTitle'

export default function StudentLayout() {
  const { user, logout } = useAuthStore()
  const navigate = useNavigate()
  const location = useLocation()
  const { isMinimized, setMinimized } = useCounselorStore()

  const isDiscoverTab = location.pathname === '/s' || location.pathname === '/s/'
  const isOtherTab = !isDiscoverTab
  const showMiniCounselor = isOtherTab && !isMinimized

  // Per-route page title (Spec/04 §15).
  const p = location.pathname
  useDocumentTitle(
    p.startsWith('/s/explore') ? 'Match'
    : p.startsWith('/s/manage') ? 'Apply'
    : p.startsWith('/s/posts') ? 'Connect'
    : p.startsWith('/s/profile') ? 'Profile'
    : p.startsWith('/s/saved') ? 'Saved'
    : p.startsWith('/s/settings') ? 'Settings'
    : p.startsWith('/s/programs') ? 'Program'
    : p.startsWith('/s/institutions') ? 'Institution'
    : p.startsWith('/s/applications') ? 'Application'
    : 'Discover',
  )

  return (
    <div className="flex flex-col h-screen bg-offwhite">
      {/* Top bar — 64px, the four journey stages (Spec/04 §7.1). */}
      <header className="h-16 flex items-center justify-between px-6 bg-white border-b border-divider flex-shrink-0 z-30">
        <NavLink to="/s" className="leading-none" aria-label="UniPaith — Discover home">
          <Wordmark className="h-7 w-auto" />
        </NavLink>

        {/* Nav — Stage 1 (Discover) → Stage 2 (Match) → Stage 3 (Apply, Connect).
            Discover gets a divider after it because it's the home / always-on
            surface for the student journey. Collapses to a hamburger < sm (§14). */}
        <nav className="hidden sm:flex items-center">
          {/* Discover — Stage 1, separated */}
          <NavLink
            to="/s"
            end
            className={({ isActive }) =>
              `flex flex-col items-center px-4 py-1.5 rounded-lg transition-colors relative ${
                isActive ? 'text-student' : 'text-slate hover:text-student-ink'
              }`
            }
          >
            {({ isActive }) => (
              <>
                <Compass size={19} />
                <span className={`text-[10px] mt-0.5 ${isActive ? 'font-semibold' : 'font-medium'}`}>Discover</span>
                {isActive && <span className="absolute bottom-0 left-2 right-2 h-0.5 bg-student rounded-full" />}
              </>
            )}
          </NavLink>

          {/* Thin divider line */}
          <div className="w-px h-8 bg-divider mx-1" />

          {/* Stage 2 → Stage 3 → Connect */}
          {[
            { to: '/s/explore', icon: Target, label: 'Match' },
            { to: '/s/manage', icon: FolderKanban, label: 'Apply' },
            { to: '/s/posts', icon: Newspaper, label: 'Connect' },
          ].map(item => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `flex flex-col items-center px-4 py-1.5 rounded-lg transition-colors relative ${
                  isActive ? 'text-student' : 'text-slate hover:text-student-ink'
                }`
              }
            >
              {({ isActive }) => (
                <>
                  <item.icon size={19} />
                  <span className={`text-[10px] mt-0.5 ${isActive ? 'font-semibold' : 'font-medium'}`}>{item.label}</span>
                  {isActive && <span className="absolute bottom-0 left-2 right-2 h-0.5 bg-student rounded-full" />}
                </>
              )}
            </NavLink>
          ))}
        </nav>

        <div className="flex items-center gap-2">
          {/* Mobile hamburger — the four stages collapse here < sm (§14). */}
          <div className="sm:hidden">
            <Dropdown
              align="right"
              trigger={
                <button className="p-2 rounded-lg hover:bg-student-mist text-slate hover:text-student-ink transition-colors" aria-label="Open navigation">
                  <Menu size={19} />
                </button>
              }
              items={[
                { label: 'Discover', onClick: () => navigate('/s'), icon: <Compass size={14} /> },
                { label: 'Match', onClick: () => navigate('/s/explore'), icon: <Target size={14} /> },
                { label: 'Apply', onClick: () => navigate('/s/manage'), icon: <FolderKanban size={14} /> },
                { label: 'Connect', onClick: () => navigate('/s/posts'), icon: <Newspaper size={14} /> },
              ]}
            />
          </div>

          <button
            onClick={() => navigate('/s/manage?tab=messages')}
            className="relative p-2 rounded-lg hover:bg-student-mist text-slate hover:text-student-ink transition-colors"
            aria-label="Messages"
          >
            <Bell size={19} />
          </button>

          <Dropdown
            align="right"
            trigger={
              <button className="p-1 rounded-lg hover:bg-student-mist transition-colors" aria-label="Account menu">
                <Avatar name={user?.email || '?'} size="sm" />
              </button>
            }
            items={[
              { label: 'Profile', onClick: () => navigate('/s/profile'), icon: <User size={14} /> },
              { label: 'Saved', onClick: () => navigate('/s/saved'), icon: <Bookmark size={14} /> },
              { label: 'Settings', onClick: () => navigate('/s/settings'), icon: <Settings size={14} /> },
              { label: 'Sign out', onClick: logout, icon: <LogOut size={14} />, variant: 'danger' },
            ]}
          />
        </div>
      </header>

      {/* Body with sliding panels */}
      <div className="flex-1 flex overflow-hidden relative">
        {/* Mini counselor panel — slides in/out on non-counselor tabs */}
        <div
          className={`flex-shrink-0 overflow-hidden transition-all duration-300 ease-in-out ${
            showMiniCounselor ? 'w-72 opacity-100' : 'w-0 opacity-0'
          }`}
        >
          <div className="w-72 h-full">
            <MiniCounselorPanel />
          </div>
        </div>

        {/* Show counselor toggle button when minimized on other tabs */}
        {isOtherTab && isMinimized && (
          <button
            onClick={() => setMinimized(false)}
            className="absolute left-0 top-3 z-20 flex items-center gap-1 pl-1.5 pr-3 py-2 bg-white border border-divider border-l-0 rounded-r-xl shadow-sm text-student hover:bg-student-mist transition-all duration-200 animate-slide-in-left"
            title="Show counselor"
          >
            <MessageSquare size={14} />
            <span className="text-[10px] font-medium">Chat</span>
          </button>
        )}

        {/* Main content area with page transition */}
        <main className="flex-1 overflow-y-auto transition-all duration-300 ease-in-out">
          <div key={location.pathname} className="animate-page-in h-full">
            <Outlet />
          </div>
        </main>
      </div>
      <CompareTray />
    </div>
  )
}
