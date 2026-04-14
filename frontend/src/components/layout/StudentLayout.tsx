import { Outlet, NavLink, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { useAuthStore } from '../../stores/auth-store'
import {
  User, Search, Sparkles, Bell, LogOut, Settings, Bookmark,
  GraduationCap, Calendar,
} from 'lucide-react'
import Avatar from '../ui/Avatar'
import Dropdown from '../ui/Dropdown'
import { getOnboarding } from '../../api/students'
import CompareTray from '../student/CompareTray'

const NAV_ITEMS = [
  { to: '/s/profile', icon: User, label: 'My Story' },
  { to: '/s/explore', icon: Search, label: 'Explore' },
  { to: '/s', icon: Sparkles, label: 'Counselor', end: true },
]

export default function StudentLayout() {
  const { user, logout } = useAuthStore()
  const navigate = useNavigate()

  const { data: onboarding } = useQuery({
    queryKey: ['onboarding'],
    queryFn: getOnboarding,
  })

  const completionPct = onboarding?.completion_percentage ?? 0

  return (
    <div className="flex flex-col h-screen bg-offwhite">
      {/* Top Navigation Bar */}
      <header className="h-14 flex items-center justify-between px-6 bg-white border-b border-divider flex-shrink-0 z-30">
        <NavLink to="/s" className="text-lg font-bold tracking-tight">
          <span className="text-student">Uni</span><span className="text-student-ink font-extrabold">Paith</span>
        </NavLink>

        <nav className="flex items-center gap-1">
          {NAV_ITEMS.map(item => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) =>
                `flex flex-col items-center px-5 py-1.5 rounded-xl transition-colors relative ${
                  isActive ? 'text-student' : 'text-slate hover:text-student-ink'
                }`
              }
            >
              {({ isActive }) => (
                <>
                  <item.icon size={20} />
                  <span className="text-[10px] mt-0.5 font-medium">{item.label}</span>
                  {isActive && (
                    <span className="absolute bottom-0 left-3 right-3 h-0.5 bg-student rounded-full" />
                  )}
                </>
              )}
            </NavLink>
          ))}
        </nav>

        <div className="flex items-center gap-2">
          <button
            onClick={() => navigate('/s')}
            className="relative p-2 rounded-xl hover:bg-student-mist text-slate hover:text-student-ink transition-colors"
          >
            <Bell size={20} />
          </button>
          <Dropdown
            trigger={
              <button className="p-1 rounded-xl hover:bg-student-mist transition-colors">
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

      <div className="flex-1 flex overflow-hidden">
        {/* Left sidebar — slim profile + quick links */}
        <aside className="w-56 flex-shrink-0 overflow-y-auto p-3 hidden lg:flex flex-col gap-3">
          {/* Profile card */}
          <div
            onClick={() => navigate('/s/profile')}
            className="bg-white rounded-xl p-3 cursor-pointer hover:shadow-sm transition-shadow border border-divider"
          >
            <div className="flex items-center gap-2.5 mb-2.5">
              <Avatar name={user?.email || '?'} size="md" />
              <div className="min-w-0">
                <p className="text-sm font-semibold text-student-ink truncate">
                  {user?.email?.split('@')[0] || 'Student'}
                </p>
                <p className="text-[10px] text-student-text">
                  {completionPct < 30 ? 'Getting started' : completionPct < 80 ? 'Building story' : 'Profile ready'}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <div className="flex-1 h-1.5 bg-student-mist rounded-full overflow-hidden">
                <div
                  className="h-full bg-student rounded-full transition-all"
                  style={{ width: `${completionPct}%` }}
                />
              </div>
              <span className="text-[10px] font-medium text-student-text">{completionPct}%</span>
            </div>
          </div>

          {/* Quick links */}
          <nav className="bg-white rounded-xl border border-divider p-2 space-y-0.5">
            {[
              { to: '/s/explore', icon: Bookmark, label: 'Saved Programs' },
              { to: '/s/profile?tab=essays', icon: GraduationCap, label: 'Essays & Resume' },
              { to: '/s/profile?tab=recommenders', icon: User, label: 'Recommenders' },
              { to: '/s/profile?tab=financial', icon: Calendar, label: 'Financial Aid' },
              { to: '/s/settings', icon: Settings, label: 'Settings' },
            ].map(link => (
              <button
                key={link.label}
                onClick={() => navigate(link.to)}
                className="w-full flex items-center gap-2 px-2.5 py-1.5 text-xs rounded-lg text-student-text hover:text-student-ink hover:bg-student-mist transition-colors"
              >
                <link.icon size={13} />
                {link.label}
              </button>
            ))}
          </nav>

          {/* Counselor nudge */}
          <div
            onClick={() => navigate('/s')}
            className="bg-white rounded-xl border border-divider p-3 cursor-pointer hover:shadow-sm transition-shadow"
          >
            <div className="flex items-center gap-2 mb-1.5">
              <Sparkles size={13} className="text-gold" />
              <p className="text-xs font-semibold text-student-ink">Your Counselor</p>
            </div>
            <p className="text-[10px] text-student-text leading-relaxed">
              Ask anything — applications, essays, deadlines, or just what to do next.
            </p>
          </div>
        </aside>

        {/* Main Content */}
        <main className="flex-1 overflow-y-auto">
          <Outlet />
        </main>
      </div>
      <CompareTray />
    </div>
  )
}
