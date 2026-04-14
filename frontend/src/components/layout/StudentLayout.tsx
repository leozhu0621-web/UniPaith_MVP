import { Outlet, NavLink, useNavigate } from 'react-router-dom'
import { useAuthStore } from '../../stores/auth-store'
import {
  User, Search, Sparkles, Bell, LogOut,
} from 'lucide-react'
import Avatar from '../ui/Avatar'
import Dropdown from '../ui/Dropdown'
import CompareTray from '../student/CompareTray'

const NAV_ITEMS = [
  { to: '/s/profile', icon: User, label: 'My Story' },
  { to: '/s/explore', icon: Search, label: 'Explore' },
  { to: '/s', icon: Sparkles, label: 'Counselor', end: true },
]

export default function StudentLayout() {
  const { user, logout } = useAuthStore()
  const navigate = useNavigate()

  return (
    <div className="flex flex-col h-screen bg-offwhite">
      {/* Top Navigation Bar */}
      <header className="h-14 flex items-center justify-between px-6 bg-white border-b border-divider flex-shrink-0 z-30">
        {/* Logo */}
        <NavLink to="/s" className="text-lg font-bold tracking-tight">
          <span className="text-student">Uni</span><span className="text-student-ink font-extrabold">Paith</span>
        </NavLink>

        {/* Center: 3 pillars */}
        <nav className="flex items-center gap-1">
          {NAV_ITEMS.map(item => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) =>
                `flex flex-col items-center px-5 py-1.5 rounded-xl transition-colors relative ${
                  isActive
                    ? 'text-student'
                    : 'text-slate hover:text-student-ink'
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

        {/* Right: bell + avatar */}
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

      {/* Main Content — full width, no sidebar */}
      <main className="flex-1 overflow-y-auto">
        <Outlet />
      </main>
      <CompareTray />
    </div>
  )
}
