import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useAuthStore } from '../../stores/auth-store'
import {
  LayoutDashboard, Users, Bug, Brain, Settings, LogOut, Shield,
} from 'lucide-react'
import clsx from 'clsx'

const navItems = [
  { to: '/admin', icon: LayoutDashboard, label: 'Dashboard', end: true },
  { to: '/admin/users', icon: Users, label: 'Users' },
  { to: '/admin/crawler', icon: Bug, label: 'Crawler' },
  { to: '/admin/ml', icon: Brain, label: 'ML Pipeline' },
  { to: '/admin/system', icon: Settings, label: 'System' },
]

export default function AdminLayout() {
  const navigate = useNavigate()
  const { logout, user } = useAuthStore()

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      <aside className="w-56 bg-gray-900 text-white flex flex-col">
        <div className="px-5 py-5 border-b border-gray-700">
          <div className="flex items-center gap-2">
            <Shield size={20} className="text-indigo-400" />
            <span className="font-bold text-lg">UniPaith</span>
          </div>
          <p className="text-xs text-gray-400 mt-1">Admin Console</p>
        </div>

        <nav className="flex-1 py-4 px-3 space-y-1">
          {navItems.map(item => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) =>
                clsx(
                  'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors',
                  isActive
                    ? 'bg-indigo-600 text-white'
                    : 'text-gray-300 hover:bg-gray-800 hover:text-white'
                )
              }
            >
              <item.icon size={18} />
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div className="px-3 pb-4 border-t border-gray-700 pt-4">
          <p className="text-xs text-gray-500 px-3 mb-2 truncate">{user?.email}</p>
          <button
            onClick={() => { logout(); navigate('/') }}
            className="flex items-center gap-3 px-3 py-2 text-sm text-red-400 hover:bg-gray-800 rounded-lg w-full"
          >
            <LogOut size={18} />
            Sign out
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-y-auto">
        <Outlet />
      </main>
    </div>
  )
}
