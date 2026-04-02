import { Outlet, NavLink, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { useAuthStore } from '../../stores/auth-store'
import {
  LayoutDashboard, MessageSquare, User, Search, FileText, Heart,
  Mail, Calendar, Clock, DollarSign, UserCheck, Settings, Bell, LogOut,
} from 'lucide-react'
import Avatar from '../ui/Avatar'
import ProgressBar from '../ui/ProgressBar'
import Dropdown from '../ui/Dropdown'
import { getOnboarding, getNextStep } from '../../api/students'
import { getUnreadCount } from '../../api/notifications'

const NAV_SECTIONS = [
  {
    label: 'Plan',
    items: [
      { to: '/s/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
      { to: '/s/chat', icon: MessageSquare, label: 'Counselor Chat' },
      { to: '/s/profile', icon: User, label: 'Profile' },
    ],
  },
  {
    label: 'Discover',
    items: [
      { to: '/s/discover', icon: Search, label: 'Discover' },
      { to: '/s/saved', icon: Heart, label: 'Saved' },
      { to: '/s/recommendations', icon: UserCheck, label: 'Recommendations' },
    ],
  },
  {
    label: 'Apply',
    items: [
      { to: '/s/applications', icon: FileText, label: 'Applications' },
      { to: '/s/calendar', icon: Calendar, label: 'Calendar' },
      { to: '/s/deadlines', icon: Clock, label: 'Deadlines' },
    ],
  },
  {
    label: 'Utility',
    items: [
      { to: '/s/messages', icon: Mail, label: 'Messages' },
      { to: '/s/financial-aid', icon: DollarSign, label: 'Financial Aid' },
      { to: '/s/settings', icon: Settings, label: 'Settings' },
    ],
  },
]

export default function StudentLayout() {
  const { user, logout } = useAuthStore()
  const navigate = useNavigate()

  const { data: onboarding } = useQuery({
    queryKey: ['onboarding'],
    queryFn: getOnboarding,
  })
  const { data: nextStep } = useQuery({
    queryKey: ['next-step'],
    queryFn: getNextStep,
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
      <aside className="w-56 flex flex-col border-r border-gray-200 bg-white py-4">
        <div className="px-4 pb-2 border-b border-gray-100">
          <p className="text-xs font-semibold uppercase tracking-wider text-gray-400">Student Journey</p>
        </div>
        <div className="flex flex-col gap-4 flex-1 px-2 pt-3">
          {NAV_SECTIONS.map(section => (
            <div key={section.label}>
              <p className="px-2 mb-1 text-[11px] font-semibold uppercase tracking-wider text-gray-400">
                {section.label}
              </p>
              {section.items.map(item => (
                <NavLink
                  key={item.to}
                  to={item.to}
                  className={({ isActive }) =>
                    `flex items-center gap-3 w-full px-2 py-2 rounded-lg transition-colors ${
                      isActive
                        ? 'bg-gray-100 text-gray-900'
                        : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50'
                    }`
                  }
                >
                  <item.icon size={18} />
                  <span className="text-sm">{item.label}</span>
                </NavLink>
              ))}
            </div>
          ))}
        </div>
      </aside>

      {/* Main content area */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Top bar */}
        <header className="flex items-center justify-between h-14 px-6 border-b border-gray-200 bg-white">
          <NavLink to="/s/dashboard" className="text-lg font-semibold text-gray-900">
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

        {/* Calm action rail */}
        <div className="px-6 py-2 border-b border-gray-100 bg-white">
          <p className="text-xs text-gray-600">
            <span className="font-medium text-gray-800">Next best action:</span>{' '}
            {nextStep?.guidance_text || 'Continue with your current application plan.'}
          </p>
        </div>

        {/* Page content */}
        <main className="flex-1 overflow-y-auto">
          <Outlet />
        </main>

        {/* Onboarding bar */}
        {completionPct < 100 && (
          <div className="flex items-center gap-4 px-6 py-3 border-t border-gray-200 bg-white">
            <ProgressBar value={completionPct} className="flex-1" />
            <span className="text-xs text-gray-600 whitespace-nowrap">
              Profile support progress: {completionPct}%
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
