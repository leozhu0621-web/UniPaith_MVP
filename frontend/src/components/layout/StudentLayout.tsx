import { Outlet, NavLink, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { useAuthStore } from '../../stores/auth-store'
import {
  LayoutDashboard, MessageSquare, User, Search, FileText,
  Calendar, Bell, LogOut, Sparkles,
} from 'lucide-react'
import Avatar from '../ui/Avatar'
import Dropdown from '../ui/Dropdown'
import { getOnboarding } from '../../api/students'
import { getUnreadCount } from '../../api/notifications'

const NAV_ITEMS = [
  { to: '/s/dashboard', icon: LayoutDashboard, label: 'Home' },
  { to: '/s/profile', icon: User, label: 'Profile' },
  { to: '/s/discover', icon: Search, label: 'Discover' },
  { to: '/s/applications', icon: FileText, label: 'Applications' },
  { to: '/s/calendar', icon: Calendar, label: 'Calendar' },
  { to: '/s/chat', icon: MessageSquare, label: 'Counselor' },
]

export default function StudentLayout() {
  const { user, logout } = useAuthStore()
  const navigate = useNavigate()

  const { data: onboarding } = useQuery({
    queryKey: ['onboarding'],
    queryFn: getOnboarding,
  })

  const { data: unreadCount } = useQuery({
    queryKey: ['unread-count'],
    queryFn: getUnreadCount,
    refetchInterval: 30000,
  })

  const hasUnread = (unreadCount?.count ?? 0) > 0
  const completionPct = onboarding?.completion_percentage ?? 0
  const milestone = completionPct < 30 ? 'Getting started' : completionPct < 60 ? 'Building momentum' : completionPct < 80 ? 'Almost there' : 'Looking strong'

  return (
    <div className="flex flex-col h-screen bg-stone-50">
      {/* Top Navigation Bar */}
      <header className="h-14 flex items-center justify-between px-6 bg-white border-b border-stone-100 flex-shrink-0 z-30">
        {/* Logo */}
        <NavLink to="/s/dashboard" className="text-lg font-bold text-stone-800 tracking-tight">
          UniPaith
        </NavLink>

        {/* Center nav icons */}
        <nav className="flex items-center gap-1">
          {NAV_ITEMS.map(item => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `flex flex-col items-center px-4 py-1.5 rounded-xl transition-colors relative ${
                  isActive
                    ? 'text-stone-800'
                    : 'text-stone-400 hover:text-stone-600'
                }`
              }
            >
              {({ isActive }) => (
                <>
                  <item.icon size={20} />
                  <span className="text-[10px] mt-0.5 font-medium">{item.label}</span>
                  {isActive && (
                    <span className="absolute bottom-0 left-2 right-2 h-0.5 bg-stone-800 rounded-full" />
                  )}
                </>
              )}
            </NavLink>
          ))}
        </nav>

        {/* Right: bell + avatar */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => navigate('/s/messages')}
            className="relative p-2 rounded-xl hover:bg-stone-100 text-stone-500 hover:text-stone-700 transition-colors"
          >
            <Bell size={20} />
            {hasUnread && (
              <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-amber-500" />
            )}
          </button>

          <Dropdown
            trigger={
              <button className="p-1 rounded-xl hover:bg-stone-100 transition-colors">
                <Avatar name={user?.email || '?'} size="sm" />
              </button>
            }
            items={[
              { label: 'Settings', onClick: () => navigate('/s/settings') },
              { label: 'Sign out', onClick: logout, icon: <LogOut size={14} />, variant: 'danger' },
            ]}
          />
        </div>
      </header>

      {/* Body: left panel + main content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Panel — Profile card + contextual shortcuts */}
        <aside className="w-60 flex-shrink-0 overflow-y-auto p-4 hidden lg:block">
          {/* Profile summary card */}
          <div
            onClick={() => navigate('/s/profile')}
            className="bg-white rounded-2xl shadow-sm p-4 cursor-pointer hover:shadow-md transition-shadow mb-4"
          >
            <div className="flex items-center gap-3 mb-3">
              <Avatar name={user?.email || '?'} size="md" />
              <div className="min-w-0">
                <p className="text-sm font-semibold text-stone-800 truncate">
                  {user?.email?.split('@')[0] || 'Student'}
                </p>
                <p className="text-xs text-stone-500">{milestone}</p>
              </div>
            </div>
            {/* Mini progress ring */}
            <div className="flex items-center gap-3">
              <div className="relative w-10 h-10 flex-shrink-0">
                <svg className="w-10 h-10 -rotate-90" viewBox="0 0 36 36">
                  <circle cx="18" cy="18" r="15" fill="none" stroke="#e7e5e4" strokeWidth="3" />
                  <circle
                    cx="18" cy="18" r="15" fill="none"
                    stroke={completionPct >= 80 ? '#059669' : completionPct >= 50 ? '#d97706' : '#78716c'}
                    strokeWidth="3"
                    strokeDasharray={`${completionPct * 0.94} 94`}
                    strokeLinecap="round"
                  />
                </svg>
                <span className="absolute inset-0 flex items-center justify-center text-[9px] font-bold text-stone-700">
                  {completionPct}%
                </span>
              </div>
              <div className="text-xs text-stone-500">
                Profile strength
              </div>
            </div>
          </div>

          {/* Quick links */}
          <div className="bg-white rounded-2xl shadow-sm p-3 mb-4">
            <p className="text-[10px] font-semibold uppercase tracking-wider text-stone-400 px-1 mb-2">Quick access</p>
            {[
              { to: '/s/saved', label: 'Saved Programs' },
              { to: '/s/recommendations', label: 'Recommenders' },
              { to: '/s/financial-aid', label: 'Financial Aid' },
              { to: '/s/messages', label: 'Messages' },
              { to: '/s/settings', label: 'Settings' },
            ].map(link => (
              <NavLink
                key={link.to}
                to={link.to}
                className={({ isActive }) =>
                  `block px-2 py-1.5 text-sm rounded-lg transition-colors ${
                    isActive
                      ? 'bg-stone-100 text-stone-800 font-medium'
                      : 'text-stone-500 hover:text-stone-700 hover:bg-stone-50'
                  }`
                }
              >
                {link.label}
              </NavLink>
            ))}
          </div>

          {/* Counselor nudge */}
          <div
            onClick={() => navigate('/s/chat')}
            className="bg-white rounded-2xl shadow-sm p-4 cursor-pointer hover:shadow-md transition-shadow"
          >
            <div className="flex items-center gap-2 mb-2">
              <Sparkles size={14} className="text-amber-500" />
              <p className="text-xs font-semibold text-stone-700">Your Counselor</p>
            </div>
            <p className="text-xs text-stone-500 leading-relaxed">
              Have a question about your journey? Your AI counselor is here to help.
            </p>
          </div>
        </aside>

        {/* Main Content */}
        <main className="flex-1 overflow-y-auto">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
