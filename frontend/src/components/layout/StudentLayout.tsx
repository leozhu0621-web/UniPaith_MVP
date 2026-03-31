import { Outlet, NavLink, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { useAuthStore } from '../../stores/auth-store'
import {
  MessageSquare, User, Search, FileText, Heart,
  Mail, Calendar, Settings, Bell, LogOut,
} from 'lucide-react'
import Avatar from '../ui/Avatar'
import ProgressBar from '../ui/ProgressBar'
import Dropdown from '../ui/Dropdown'
import { getOnboarding } from '../../api/students'
import { getUnreadCount } from '../../api/notifications'

const NAV_ITEMS = [
  { to: '/s/chat', icon: MessageSquare, label: 'Chat' },
  { to: '/s/profile', icon: User, label: 'Profile' },
  { to: '/s/discover', icon: Search, label: 'Discover' },
  { to: '/s/applications', icon: FileText, label: 'Applications' },
  { to: '/s/saved', icon: Heart, label: 'Saved' },
  { to: '/s/messages', icon: Mail, label: 'Messages' },
  { to: '/s/calendar', icon: Calendar, label: 'Calendar' },
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

  const completionPct = onboarding?.completion_percentage ?? 0

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Nav rail */}
      <aside className="w-16 flex flex-col items-center border-r border-gray-200 bg-white py-4">
        <div className="flex flex-col gap-1 flex-1">
          {NAV_ITEMS.map(item => (
            <NavLink
              key={item.to}
              to={item.to}
              title={item.label}
              className={({ isActive }) =>
                `flex items-center justify-center w-10 h-10 rounded-lg transition-colors ${
                  isActive
                    ? 'bg-gray-100 text-gray-900'
                    : 'text-gray-400 hover:text-gray-600 hover:bg-gray-50'
                }`
              }
            >
              <item.icon size={20} />
            </NavLink>
          ))}
        </div>
        <div className="border-t border-gray-200 pt-2 mt-2">
          <NavLink
            to="/s/settings"
            title="Settings"
            className={({ isActive }) =>
              `flex items-center justify-center w-10 h-10 rounded-lg transition-colors ${
                isActive
                  ? 'bg-gray-100 text-gray-900'
                  : 'text-gray-400 hover:text-gray-600 hover:bg-gray-50'
              }`
            }
          >
            <Settings size={20} />
          </NavLink>
        </div>
      </aside>

      {/* Main content area */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Top bar */}
        <header className="flex items-center justify-between h-14 px-6 border-b border-gray-200 bg-white">
          <NavLink to="/s/chat" className="text-lg font-semibold text-gray-900">
            UniPaith
          </NavLink>
          <div className="flex items-center gap-3">
            {/* Notification bell */}
            <button
              onClick={() => navigate('/s/settings')}
              className="relative p-2 rounded-lg hover:bg-gray-100"
            >
              <Bell size={18} className="text-gray-600" />
              {(unreadCount?.count ?? 0) > 0 && (
                <span className="absolute top-1 right-1 w-4 h-4 rounded-full bg-red-500 text-white text-[10px] flex items-center justify-center">
                  {unreadCount.count > 9 ? '9+' : unreadCount.count}
                </span>
              )}
            </button>

            {/* User dropdown */}
            <Dropdown
              trigger={
                <button className="flex items-center gap-2 px-2 py-1 rounded-lg hover:bg-gray-100">
                  <Avatar name={user?.email || '?'} size="sm" />
                </button>
              }
              items={[
                { label: 'Profile', onClick: () => navigate('/s/profile') },
                { label: 'Settings', onClick: () => navigate('/s/settings') },
                { label: 'Sign out', onClick: logout, icon: <LogOut size={14} />, variant: 'danger' },
              ]}
            />
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1 overflow-y-auto">
          <Outlet />
        </main>

        {/* Onboarding bar */}
        {completionPct < 100 && (
          <div className="flex items-center gap-4 px-6 py-3 border-t border-gray-200 bg-white">
            <ProgressBar value={completionPct} className="flex-1" />
            <span className="text-xs text-gray-600 whitespace-nowrap">
              Profile {completionPct}% complete
            </span>
            <button
              onClick={() => navigate('/s/profile')}
              className="text-xs font-medium text-gray-900 hover:underline whitespace-nowrap"
            >
              Complete
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
