import { Outlet, NavLink, useNavigate } from 'react-router-dom'
import { useAuthStore } from '../../stores/auth-store'
import {
  Sparkles, Newspaper, Search, FolderKanban,
  Bell, LogOut, User, Bookmark, Settings,
} from 'lucide-react'
import Avatar from '../ui/Avatar'
import Dropdown from '../ui/Dropdown'
import CompareTray from '../student/CompareTray'

const NAV_ITEMS = [
  { to: '/s', icon: Sparkles, label: 'Counselor', end: true },
  { to: '/s/posts', icon: Newspaper, label: 'Posts' },
  { to: '/s/explore', icon: Search, label: 'Explore' },
  { to: '/s/manage', icon: FolderKanban, label: 'Management' },
]

export default function StudentLayout() {
  const { user, logout } = useAuthStore()
  const navigate = useNavigate()

  return (
    <div className="flex flex-col h-screen bg-offwhite">
      {/* Top bar */}
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
                `flex flex-col items-center px-4 py-1.5 rounded-lg transition-colors relative ${
                  isActive ? 'text-student' : 'text-slate hover:text-student-ink'
                }`
              }
            >
              {({ isActive }) => (
                <>
                  <item.icon size={19} />
                  <span className="text-[10px] mt-0.5 font-medium">{item.label}</span>
                  {isActive && (
                    <span className="absolute bottom-0 left-2 right-2 h-0.5 bg-student rounded-full" />
                  )}
                </>
              )}
            </NavLink>
          ))}
        </nav>

        <div className="flex items-center gap-2">
          <button
            onClick={() => navigate('/s/manage?tab=messages')}
            className="relative p-2 rounded-lg hover:bg-student-mist text-slate hover:text-student-ink transition-colors"
          >
            <Bell size={19} />
          </button>

          <Dropdown
            trigger={
              <button className="p-1 rounded-lg hover:bg-student-mist transition-colors">
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

      {/* Main content — each page owns its own layout (sidebars, splits, etc.) */}
      <main className="flex-1 overflow-hidden">
        <Outlet />
      </main>
      <CompareTray />
    </div>
  )
}
