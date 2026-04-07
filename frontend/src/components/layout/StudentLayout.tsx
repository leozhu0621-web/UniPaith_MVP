import { useState, useEffect, useRef } from 'react'
import { Outlet, NavLink, useNavigate, useLocation } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { useAuthStore } from '../../stores/auth-store'
import {
  LayoutDashboard, MessageSquare, User, Search, FileText,
  Calendar, Bell, LogOut, ChevronRight,
} from 'lucide-react'
import Avatar from '../ui/Avatar'
import Dropdown from '../ui/Dropdown'
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
  const location = useLocation()
  const [expanded, setExpanded] = useState(false)
  const sidebarRef = useRef<HTMLElement>(null)

  const { data: unreadCount } = useQuery({
    queryKey: ['unread-count'],
    queryFn: getUnreadCount,
    refetchInterval: 30000,
  })

  const hasUnread = (unreadCount?.count ?? 0) > 0

  // Collapse sidebar on route change
  useEffect(() => {
    setExpanded(false)
  }, [location.pathname])

  // Collapse sidebar on outside click
  useEffect(() => {
    const handleClick = (e: MouseEvent) => {
      if (sidebarRef.current && !sidebarRef.current.contains(e.target as Node)) {
        setExpanded(false)
      }
    }
    if (expanded) {
      document.addEventListener('mousedown', handleClick)
      return () => document.removeEventListener('mousedown', handleClick)
    }
  }, [expanded])

  return (
    <div className="flex h-screen bg-stone-50">
      {/* Sidebar */}
      <aside
        ref={sidebarRef}
        className={`fixed top-0 left-0 h-full z-40 flex flex-col bg-stone-50 transition-all duration-200 ease-in-out ${
          expanded ? 'w-52 shadow-xl bg-white' : 'w-14'
        }`}
      >
        {/* Logo / expand toggle */}
        <div className="h-14 flex items-center justify-center flex-shrink-0">
          <button
            onClick={() => setExpanded(e => !e)}
            className="p-2 rounded-xl hover:bg-stone-100 transition-colors"
          >
            <ChevronRight
              size={18}
              className={`text-stone-400 transition-transform duration-200 ${expanded ? 'rotate-180' : ''}`}
            />
          </button>
        </div>

        {/* Nav items */}
        <nav className="flex-1 flex flex-col gap-1 px-2 pt-2">
          {NAV_ITEMS.map(item => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `flex items-center gap-3 rounded-xl transition-colors ${
                  expanded ? 'px-3 py-2.5' : 'justify-center py-2.5'
                } ${
                  isActive
                    ? 'bg-stone-200/70 text-stone-900'
                    : 'text-stone-500 hover:text-stone-700 hover:bg-stone-100'
                }`
              }
              title={!expanded ? item.label : undefined}
            >
              <item.icon size={20} className="flex-shrink-0" />
              {expanded && <span className="text-sm font-medium">{item.label}</span>}
            </NavLink>
          ))}
        </nav>

        {/* Bottom: notification + avatar */}
        <div className={`flex flex-col gap-1 px-2 pb-4 ${expanded ? '' : 'items-center'}`}>
          {/* Notification bell */}
          <button
            onClick={() => navigate('/s/messages')}
            className={`relative flex items-center gap-3 rounded-xl transition-colors text-stone-500 hover:text-stone-700 hover:bg-stone-100 ${
              expanded ? 'px-3 py-2.5' : 'justify-center py-2.5'
            }`}
            title={!expanded ? 'Messages' : undefined}
          >
            <Bell size={20} className="flex-shrink-0" />
            {hasUnread && (
              <span className="absolute top-1.5 left-6 w-2 h-2 rounded-full bg-amber-500" />
            )}
            {expanded && <span className="text-sm font-medium">Messages</span>}
          </button>

          {/* Avatar / user menu */}
          <Dropdown
            trigger={
              <button
                className={`flex items-center gap-3 rounded-xl transition-colors hover:bg-stone-100 ${
                  expanded ? 'px-3 py-2.5 w-full' : 'justify-center py-2.5'
                }`}
              >
                <Avatar name={user?.email || '?'} size="sm" />
                {expanded && (
                  <span className="text-sm text-stone-600 truncate">{user?.email?.split('@')[0]}</span>
                )}
              </button>
            }
            items={[
              { label: 'Settings', onClick: () => navigate('/s/settings') },
              { label: 'Sign out', onClick: logout, icon: <LogOut size={14} />, variant: 'danger' },
            ]}
          />
        </div>
      </aside>

      {/* Main content area */}
      <div className={`flex-1 flex flex-col min-w-0 transition-all duration-200 ${expanded ? 'ml-52' : 'ml-14'}`}>
        <main className="flex-1 overflow-y-auto">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
