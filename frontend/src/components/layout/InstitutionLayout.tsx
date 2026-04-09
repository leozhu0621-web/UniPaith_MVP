import { useEffect, useMemo, useRef, useState } from 'react'
import { Outlet, NavLink, useNavigate, useLocation } from 'react-router-dom'
import { useAuthStore } from '../../stores/auth-store'
import { useUIStore } from '../../stores/ui-store'
import {
  LayoutDashboard, GraduationCap, Kanban, Video, Inbox, Star, ScrollText, FileStack, CalendarRange, ClipboardList,
  MessageSquare, Users, Megaphone, CalendarDays, BarChart3, FileText,
  Settings, ChevronLeft, ChevronRight, Bell, Search, LogOut, Rocket, Command, Upload,
} from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import { getUnreadCount } from '../../api/notifications'
import { getInstitution } from '../../api/institutions'
import Modal from '../ui/Modal'
import Input from '../ui/Input'

const buildNavSections = (showSetup: boolean) => [
  {
    label: 'Today',
    items: [
      { to: '/i/dashboard', icon: LayoutDashboard, label: 'Overview' },
      ...(showSetup ? [{ to: '/i/setup', icon: Rocket, label: 'Get Started' }] : []),
    ],
  },
  {
    label: 'Programs',
    items: [
      { to: '/i/programs', icon: GraduationCap, label: 'Programs' },
      { to: '/i/intake-rounds', icon: CalendarRange, label: 'Intake Rounds' },
      { to: '/i/requirements', icon: ClipboardList, label: 'Requirements' },
    ],
  },
  {
    label: 'Pipeline',
    items: [
      { to: '/i/pipeline', icon: Kanban, label: 'Applications' },
      { to: '/i/cohort-compare', icon: Users, label: 'Cohort Compare' },
      { to: '/i/interviews', icon: Video, label: 'Interviews' },
      { to: '/i/messages', icon: MessageSquare, label: 'Inbox' },
    ],
  },
  {
    label: 'Outreach',
    items: [
      { to: '/i/campaigns', icon: Megaphone, label: 'Campaigns' },
      { to: '/i/segments', icon: Users, label: 'Segments' },
      { to: '/i/events', icon: CalendarDays, label: 'Events' },
      { to: '/i/posts', icon: FileText, label: 'Posts' },
      { to: '/i/inquiries', icon: Inbox, label: 'Inquiries' },
      { to: '/i/promotions', icon: Star, label: 'Promotions' },
      { to: '/i/templates', icon: FileStack, label: 'Templates' },
    ],
  },
  {
    label: 'Insights',
    items: [
      { to: '/i/analytics', icon: BarChart3, label: 'Analytics' },
      { to: '/i/audit-log', icon: ScrollText, label: 'Audit Log' },
    ],
  },
  {
    label: 'Settings',
    items: [
      { to: '/i/data', icon: Upload, label: 'Data' },
      { to: '/i/settings', icon: Settings, label: 'Settings' },
    ],
  },
]

export default function InstitutionLayout() {
  const { user, logout } = useAuthStore()
  const { sidebarCollapsed, toggleSidebar } = useUIStore()
  const navigate = useNavigate()
  const location = useLocation()
  const sidebarWidth = sidebarCollapsed ? 'w-16' : 'w-60'
  const [showCommandPalette, setShowCommandPalette] = useState(false)
  const [showNotificationsMenu, setShowNotificationsMenu] = useState(false)
  const [showUserMenu, setShowUserMenu] = useState(false)
  const [commandQuery, setCommandQuery] = useState('')
  const shortcutPrefixAtRef = useRef<number | null>(null)
  const notificationsMenuRef = useRef<HTMLDivElement | null>(null)
  const userMenuRef = useRef<HTMLDivElement | null>(null)

  const { data: unreadCount } = useQuery({
    queryKey: ['unread-count'],
    queryFn: getUnreadCount,
    refetchInterval: 30000,
  })
  const institutionQ = useQuery({
    queryKey: ['institution'],
    queryFn: getInstitution,
    retry: false,
  })
  const institutionMissing =
    institutionQ.isError &&
    institutionQ.error instanceof Error &&
    /not found|no institution|404/i.test(institutionQ.error.message)

  useEffect(() => {
    if (!institutionMissing) return
    if (location.pathname === '/i/setup') return
    navigate('/i/setup', { replace: true })
  }, [institutionMissing, location.pathname, navigate])

  const navSections = buildNavSections(institutionQ.isError)
  const currentArea =
    navSections.flatMap(section => section.items).find(item => location.pathname.startsWith(item.to))?.label ?? 'Overview'
  const currentSection =
    navSections.find(section => section.items.some(item => location.pathname.startsWith(item.to)))?.label ?? 'Today'
  const commandActions = useMemo(() => [
    { id: 'go-overview', label: 'Go to Overview', hint: 'g o', onSelect: () => navigate('/i/dashboard') },
    { id: 'go-programs', label: 'Go to Programs', hint: 'g p', onSelect: () => navigate('/i/programs') },
    { id: 'go-apps-review', label: 'Open Review Queue', hint: 'g r', onSelect: () => navigate('/i/pipeline?tab=review') },
    { id: 'go-apps-board', label: 'Open Applications Board', hint: 'g a', onSelect: () => navigate('/i/pipeline?tab=board') },
    { id: 'go-interviews', label: 'Go to Interviews', hint: 'g i', onSelect: () => navigate('/i/interviews') },
    { id: 'go-campaigns', label: 'Go to Campaigns', hint: 'g c', onSelect: () => navigate('/i/campaigns') },
    { id: 'go-events', label: 'Go to Events', hint: 'g e', onSelect: () => navigate('/i/events') },
    { id: 'go-insights', label: 'Go to Insights', hint: 'g s', onSelect: () => navigate('/i/analytics') },
  ], [navigate])
  const filteredActions = useMemo(() => {
    const q = commandQuery.trim().toLowerCase()
    if (!q) return commandActions
    return commandActions.filter(action =>
      action.label.toLowerCase().includes(q) || action.hint.toLowerCase().includes(q)
    )
  }, [commandActions, commandQuery])

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k') {
        event.preventDefault()
        setShowCommandPalette(true)
        return
      }
      if (event.key === 'Escape') {
        setShowCommandPalette(false)
        return
      }
      if (event.target instanceof HTMLInputElement || event.target instanceof HTMLTextAreaElement) return
      if (event.key.toLowerCase() === 'g') {
        shortcutPrefixAtRef.current = Date.now()
        return
      }
      const prefix = shortcutPrefixAtRef.current
      if (!prefix) return
      if (Date.now() - prefix > 1400) {
        shortcutPrefixAtRef.current = null
        return
      }
      const key = event.key.toLowerCase()
      const shortcutMap: Record<string, () => void> = {
        o: () => navigate('/i/dashboard'),
        p: () => navigate('/i/programs'),
        r: () => navigate('/i/pipeline?tab=review'),
        a: () => navigate('/i/pipeline?tab=board'),
        i: () => navigate('/i/interviews'),
        c: () => navigate('/i/campaigns'),
        e: () => navigate('/i/events'),
        s: () => navigate('/i/analytics'),
      }
      if (shortcutMap[key]) {
        event.preventDefault()
        shortcutMap[key]()
      }
      shortcutPrefixAtRef.current = null
    }
    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [navigate])

  useEffect(() => {
    const handleOutsideClick = (event: MouseEvent) => {
      const target = event.target as Node
      if (notificationsMenuRef.current && !notificationsMenuRef.current.contains(target)) {
        setShowNotificationsMenu(false)
      }
      if (userMenuRef.current && !userMenuRef.current.contains(target)) {
        setShowUserMenu(false)
      }
    }
    document.addEventListener('mousedown', handleOutsideClick)
    return () => document.removeEventListener('mousedown', handleOutsideClick)
  }, [])

  return (
    <div className="flex h-screen bg-institution">
      {/* Sidebar */}
      <aside className={`${sidebarWidth} flex flex-col border-r border-gray-200 bg-white transition-all duration-200`}>
        <div className="flex items-center justify-between h-14 px-4 border-b border-gray-100">
          {!sidebarCollapsed && (
            <span className="text-lg font-bold">
              <span className="text-brand-slate-600">Uni</span><span className="text-brand-slate-800 font-extrabold">Paith</span>
            </span>
          )}
          <button onClick={toggleSidebar} className="p-1 rounded hover:bg-gray-100">
            {sidebarCollapsed ? <ChevronRight size={18} /> : <ChevronLeft size={18} />}
          </button>
        </div>

        <nav className="flex-1 overflow-y-auto py-4">
          {navSections.map(section => (
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
                        ? 'bg-brand-slate-50 text-brand-slate-700 font-medium'
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
        <header className="sticky top-0 z-10 flex items-center justify-between h-14 px-6 border-b border-gray-200 bg-white/95 backdrop-blur supports-[backdrop-filter]:bg-white/90">
          <div className="flex items-center gap-4">
            <div className="hidden md:flex items-center gap-2">
              <span className="px-2 py-1 rounded-md text-[11px] font-semibold uppercase tracking-wide bg-brand-slate-50 text-brand-slate-700">
                {currentSection}
              </span>
              <span className="text-sm font-medium text-gray-700">{currentArea}</span>
            </div>
            <div className="relative">
              <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
              <input
                type="text"
                placeholder="Global search (coming soon)"
                disabled
                className="w-72 pl-9 pr-4 py-1.5 text-sm border border-gray-200 rounded-lg text-gray-400 bg-gray-50 cursor-not-allowed"
              />
            </div>
            <button
              onClick={() => setShowCommandPalette(true)}
              className="hidden lg:flex items-center gap-2 px-2.5 py-1.5 text-xs border border-gray-200 rounded-md text-gray-600 hover:bg-gray-50"
            >
              <Command size={14} />
              Quick Actions
              <span className="text-[10px] text-gray-400">Ctrl/Cmd+K</span>
            </button>
          </div>

          <div className="flex items-center gap-4">
            <div className="relative" ref={notificationsMenuRef}>
              <button
                type="button"
                onClick={() => {
                  setShowNotificationsMenu(v => !v)
                  setShowUserMenu(false)
                }}
                className="relative p-2 rounded-lg hover:bg-gray-100"
              >
                <Bell size={18} className="text-gray-600" />
                {(unreadCount?.count ?? 0) > 0 && (
                  <span className="absolute top-1 right-1 w-4 h-4 rounded-full bg-red-500 text-white text-[10px] flex items-center justify-center">
                    {unreadCount.count > 9 ? '9+' : unreadCount.count}
                  </span>
                )}
              </button>
              {showNotificationsMenu && (
                <div className="absolute right-0 top-full mt-1 w-60 bg-white border border-gray-200 rounded-lg shadow-lg py-1 z-50">
                  <div className="px-3 py-2 text-xs text-gray-500 border-b border-gray-100">
                    {unreadCount?.count ?? 0} unread notifications
                  </div>
                  <button
                    type="button"
                    onClick={() => {
                      navigate('/i/messages')
                      setShowNotificationsMenu(false)
                    }}
                    className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
                  >
                    Open inbox
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      navigate('/i/settings?tab=notifications')
                      setShowNotificationsMenu(false)
                    }}
                    className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
                  >
                    Notification settings
                  </button>
                </div>
              )}
            </div>

            <div className="relative" ref={userMenuRef}>
              <button
                type="button"
                onClick={() => {
                  setShowUserMenu(v => !v)
                  setShowNotificationsMenu(false)
                }}
                className="flex items-center gap-2 px-3 py-1.5 rounded-lg hover:bg-gray-100"
              >
                <div className="w-7 h-7 rounded-full bg-brand-slate-100 flex items-center justify-center text-xs font-medium text-brand-slate-700">
                  {user?.email?.charAt(0).toUpperCase()}
                </div>
                {!sidebarCollapsed && (
                  <span className="text-sm text-gray-700">{user?.email}</span>
                )}
              </button>
              {showUserMenu && (
                <div className="absolute right-0 top-full mt-1 w-48 bg-white border border-gray-200 rounded-lg shadow-lg py-1 z-50">
                  <button
                    type="button"
                    onClick={() => {
                      navigate('/i/settings')
                      setShowUserMenu(false)
                    }}
                    className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
                  >
                    Settings
                  </button>
                  <button
                    type="button"
                    onClick={logout}
                    className="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50 flex items-center gap-2"
                  >
                    <LogOut size={14} /> Sign out
                  </button>
                </div>
              )}
            </div>
          </div>
        </header>

        <main className="flex-1 overflow-y-auto">
          <Outlet />
        </main>
      </div>
      <Modal
        isOpen={showCommandPalette}
        onClose={() => {
          setShowCommandPalette(false)
          setCommandQuery('')
        }}
        title="Quick Actions"
      >
        <div className="space-y-3">
          <Input
            value={commandQuery}
            onChange={e => setCommandQuery(e.target.value)}
            placeholder="Search action or shortcut (example: review, g r)"
          />
          <div className="max-h-72 overflow-y-auto space-y-1">
            {filteredActions.length === 0 ? (
              <p className="text-sm text-gray-500 py-3 text-center">No actions found.</p>
            ) : (
              filteredActions.map(action => (
                <button
                  key={action.id}
                  onClick={() => {
                    action.onSelect()
                    setShowCommandPalette(false)
                    setCommandQuery('')
                  }}
                  className="w-full flex items-center justify-between px-3 py-2 text-sm rounded-md hover:bg-gray-50 text-left"
                >
                  <span className="text-gray-700">{action.label}</span>
                  <span className="text-[11px] text-gray-400">{action.hint}</span>
                </button>
              ))
            )}
          </div>
        </div>
      </Modal>
    </div>
  )
}
