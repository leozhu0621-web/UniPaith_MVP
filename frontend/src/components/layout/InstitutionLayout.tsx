import { Outlet, NavLink, useNavigate } from 'react-router-dom'
import { useAuthStore } from '../../stores/auth-store'
import { useUIStore } from '../../stores/ui-store'
import {
  LayoutDashboard, GraduationCap, Kanban, FileCheck, Video,
  MessageSquare, Users, Megaphone, CalendarDays, BarChart3,
  Settings, ChevronLeft, ChevronRight, Bell, Search, LogOut,
} from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import { getUnreadCount } from '../../api/notifications'

const NAV_SECTIONS = [
  {
    label: 'Core',
    items: [
      { to: '/i/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
      { to: '/i/programs', icon: GraduationCap, label: 'Programs' },
      { to: '/i/pipeline', icon: Kanban, label: 'Pipeline' },
      { to: '/i/reviews', icon: FileCheck, label: 'Reviews' },
      { to: '/i/interviews', icon: Video, label: 'Interviews' },
      { to: '/i/messages', icon: MessageSquare, label: 'Messages' },
    ],
  },
  {
    label: 'Outreach',
    items: [
      { to: '/i/segments', icon: Users, label: 'Segments' },
      { to: '/i/campaigns', icon: Megaphone, label: 'Campaigns' },
      { to: '/i/events', icon: CalendarDays, label: 'Events' },
    ],
  },
  {
    label: 'Admin',
    items: [
      { to: '/i/analytics', icon: BarChart3, label: 'Analytics' },
      { to: '/i/settings', icon: Settings, label: 'Settings' },
    ],
  },
]

export default function InstitutionLayout() {
  const { user, logout } = useAuthStore()
  const { sidebarCollapsed, toggleSidebar } = useUIStore()
  const navigate = useNavigate()
  const sidebarWidth = sidebarCollapsed ? 'w-16' : 'w-60'

  const { data: unreadCount } = useQuery({
    queryKey: ['unread-count'],
    queryFn: getUnreadCount,
    refetchInterval: 30000,
  })

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      <aside className={`${sidebarWidth} flex flex-col border-r border-gray-200 bg-white transition-all duration-200`}>
        <div className="flex items-center justify-between h-14 px-4 border-b border-gray-100">
          {!sidebarCollapsed && (
            <span className="text-lg font-bold text-indigo-600">UniPaith</span>
          )}
          <button onClick={toggleSidebar} className="p-1 rounded hover:bg-gray-100">
            {sidebarCollapsed ? <ChevronRight size={18} /> : <ChevronLeft size={18} />}
          </button>
        </div>

        <nav className="flex-1 overflow-y-auto py-4">
          {NAV_SECTIONS.map(section => (
            <div key={section.label} className="mb-4">
              {!sidebarCollapsed && (
                <div className="px-4 mb-1 text-[11px] font-semibold uppercase tracking-wider text-gray-400">
                  {section.label}
                </div>
              )}
              {section.items.map(item => (
                <NavLink
                  key={item.to}
                  to={item.to}
                  className={({ isActive }) =>
                    `flex items-center gap-3 px-4 py-2 mx-2 rounded-md text-sm transition-colors ${
                      isActive
                        ? 'bg-indigo-50 text-indigo-700 font-medium'
                        : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                    }`
                  }
                >
                  <item.icon size={18} />
                  {!sidebarCollapsed && <span>{item.label}</span>}
                </NavLink>
              ))}
            </div>
          ))}
        </nav>
      </aside>

      {/* Main content area */}
      <div className="flex-1 flex flex-col min-w-0">
        <header className="flex items-center justify-between h-14 px-6 border-b border-gray-200 bg-white">
          <div className="flex items-center gap-4">
            <div className="relative">
              <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
              <input
                type="text"
                placeholder="Search students, programs..."
                className="w-72 pl-9 pr-4 py-1.5 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
              />
            </div>
          </div>

          <div className="flex items-center gap-4">
            <button className="relative p-2 rounded-lg hover:bg-gray-100">
              <Bell size={18} className="text-gray-600" />
              {(unreadCount?.count ?? 0) > 0 && (
                <span className="absolute top-1 right-1 w-4 h-4 rounded-full bg-red-500 text-white text-[10px] flex items-center justify-center">
                  {unreadCount.count > 9 ? '9+' : unreadCount.count}
                </span>
              )}
            </button>

            <div className="relative group">
              <button className="flex items-center gap-2 px-3 py-1.5 rounded-lg hover:bg-gray-100">
                <div className="w-7 h-7 rounded-full bg-indigo-100 flex items-center justify-center text-xs font-medium text-indigo-700">
                  {user?.email?.charAt(0).toUpperCase()}
                </div>
                {!sidebarCollapsed && (
                  <span className="text-sm text-gray-700">{user?.email}</span>
                )}
              </button>
              <div className="hidden group-hover:block absolute right-0 top-full mt-1 w-48 bg-white border border-gray-200 rounded-lg shadow-lg py-1 z-50">
                <button
                  onClick={() => navigate('/i/settings')}
                  className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
                >
                  Settings
                </button>
                <button
                  onClick={logout}
                  className="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50 flex items-center gap-2"
                >
                  <LogOut size={14} /> Sign out
                </button>
              </div>
            </div>
          </div>
        </header>

        <main className="flex-1 overflow-y-auto">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
