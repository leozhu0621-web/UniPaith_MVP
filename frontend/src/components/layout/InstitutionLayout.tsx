import { useEffect, useMemo, useRef, useState } from 'react'
import { Outlet, NavLink, useNavigate, useLocation } from 'react-router-dom'
import { useAuthStore } from '../../stores/auth-store'
import { useUIStore } from '../../stores/ui-store'
import {
  LayoutDashboard, GraduationCap, Kanban, Megaphone, MessageSquare,
  BarChart3, Settings, ChevronLeft, ChevronRight, Bell, Search, LogOut,
  Rocket, Command, ChevronDown, Menu, X,
} from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import { getUnreadCount } from '../../api/notifications'
import { getInstitution, getInstitutionPrograms } from '../../api/institutions'
import Modal from '../ui/Modal'
import Input from '../ui/Input'
import Wordmark from '../ui/Wordmark'

const buildNavSections = (showSetup: boolean) => [
  {
    label: '',
    items: [
      { to: '/i/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
      ...(showSetup ? [{ to: '/i/setup', icon: Rocket, label: 'Get Started' }] : []),
    ],
  },
  {
    label: 'Manage',
    items: [
      { to: '/i/programs', icon: GraduationCap, label: 'Programs' },
      { to: '/i/admissions', icon: Kanban, label: 'Admissions' },
      { to: '/i/outreach', icon: Megaphone, label: 'Outreach' },
      { to: '/i/communications', icon: MessageSquare, label: 'Communications' },
    ],
  },
  {
    label: 'Analyze',
    items: [
      { to: '/i/analytics', icon: BarChart3, label: 'Analytics' },
    ],
  },
  {
    label: '',
    items: [
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
  const [mobileNavOpen, setMobileNavOpen] = useState(false)
  const [commandQuery, setCommandQuery] = useState('')
  const shortcutPrefixAtRef = useRef<number | null>(null)
  const notificationsMenuRef = useRef<HTMLDivElement | null>(null)
  const userMenuRef = useRef<HTMLDivElement | null>(null)

  const { selectedProgramId, selectedProgramName, setSelectedProgram } = useUIStore()
  const [showProgramList, setShowProgramList] = useState(false)

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
  const programsQ = useQuery({
    queryKey: ['institution-programs'],
    queryFn: getInstitutionPrograms,
  })
  const programs = Array.isArray(programsQ.data) ? programsQ.data : []
  const institutionMissing =
    institutionQ.isError &&
    institutionQ.error instanceof Error &&
    /not found|no institution|404/i.test(institutionQ.error.message)

  useEffect(() => {
    if (!institutionMissing) return
    if (location.pathname === '/i/setup') return
    navigate('/i/setup', { replace: true })
  }, [institutionMissing, location.pathname, navigate])

  // Close the mobile nav whenever the route changes.
  useEffect(() => {
    setMobileNavOpen(false)
  }, [location.pathname])

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

  const programSwitcher = (compact: boolean) =>
    programs.length > 0 && (
      <div className="px-3 py-2 border-b border-border">
        <button
          onClick={() => setShowProgramList(!showProgramList)}
          className="w-full flex items-center justify-between px-2 py-1.5 rounded-md text-sm bg-muted hover:brightness-95 transition-all"
        >
          <span className="truncate font-medium text-foreground">{selectedProgramName || 'All Programs'}</span>
          <ChevronDown size={14} className={`text-muted-foreground transition-transform ${showProgramList ? 'rotate-180' : ''}`} />
        </button>
        {showProgramList && (
          <div className="mt-1 max-h-48 overflow-y-auto space-y-0.5">
            <button
              onClick={() => { setSelectedProgram(null); setShowProgramList(false) }}
              className={`w-full text-left px-2 py-1 rounded text-xs transition-colors ${!selectedProgramId ? 'bg-cobalt/10 text-cobalt font-medium' : 'text-muted-foreground hover:bg-muted'}`}
            >
              All Programs
            </button>
            {programs.map((p: any) => (
              <button
                key={p.id}
                onClick={() => { setSelectedProgram(p.id, p.program_name); setShowProgramList(false); if (compact) setMobileNavOpen(false) }}
                className={`w-full text-left px-2 py-1 rounded text-xs flex items-center gap-1.5 transition-colors ${selectedProgramId === p.id ? 'bg-cobalt/10 text-cobalt font-medium' : 'text-muted-foreground hover:bg-muted'}`}
              >
                <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${p.is_published ? 'bg-success' : 'bg-border'}`} />
                <span className="truncate">{p.program_name}</span>
              </button>
            ))}
          </div>
        )}
      </div>
    )

  const navList = (collapsed: boolean) => (
    <nav className="flex-1 overflow-y-auto py-3">
      {navSections.map(section => (
        <div key={section.label || 'root'} className={section.label ? 'mb-3' : 'mb-1'}>
          {!collapsed && section.label && (
            <div className="px-4 mb-1 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
              {section.label}
            </div>
          )}
          {section.items.map(item => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `touch-target flex items-center gap-3 px-4 py-2 mx-2 rounded-md text-sm transition-colors ${
                  isActive
                    ? 'bg-cobalt/10 text-cobalt font-medium'
                    : 'text-muted-foreground hover:bg-muted hover:text-foreground'
                }`
              }
            >
              <item.icon size={18} />
              {!collapsed && <span>{item.label}</span>}
            </NavLink>
          ))}
        </div>
      ))}
    </nav>
  )

  return (
    <div className="flex h-screen bg-background">
      {/* ─── Desktop sidebar (lg+) ─── */}
      <aside className={`${sidebarWidth} hidden lg:flex flex-col border-r border-border bg-card transition-all duration-200`}>
        <div className="flex items-center justify-between h-14 px-4 border-b border-border">
          {!sidebarCollapsed && <Wordmark className="h-6 w-auto" />}
          <button onClick={toggleSidebar} aria-label="Toggle sidebar" className="ui-btn p-1 rounded hover:bg-muted text-muted-foreground">
            {sidebarCollapsed ? <ChevronRight size={18} /> : <ChevronLeft size={18} />}
          </button>
        </div>
        {!sidebarCollapsed && programSwitcher(false)}
        {navList(sidebarCollapsed)}
      </aside>

      {/* ─── Mobile nav sheet (< lg) — Spec/02b §3.2 ─── */}
      {mobileNavOpen && (
        <div className="lg:hidden fixed inset-0 z-50 flex">
          <div className="fixed inset-0" style={{ background: 'rgba(10, 20, 40, 0.45)' }} onClick={() => setMobileNavOpen(false)} />
          <div className="relative w-72 max-w-[85vw] h-full bg-card border-r border-border flex flex-col animate-slide-in-left">
            <div className="flex items-center justify-between h-14 px-4 border-b border-border">
              <Wordmark className="h-6 w-auto" />
              <button onClick={() => setMobileNavOpen(false)} aria-label="Close menu" className="ui-btn p-1.5 rounded hover:bg-muted text-muted-foreground">
                <X size={18} />
              </button>
            </div>
            {programSwitcher(true)}
            {navList(false)}
          </div>
        </div>
      )}

      {/* Main content area */}
      <div className="flex-1 flex flex-col min-w-0">
        <header className="sticky top-0 z-10 flex items-center justify-between h-14 px-4 sm:px-6 border-b border-border bg-card/95 backdrop-blur supports-[backdrop-filter]:bg-card/90">
          <div className="flex items-center gap-3 min-w-0">
            <button
              onClick={() => setMobileNavOpen(true)}
              aria-label="Open menu"
              className="ui-btn lg:hidden p-2 -ml-1 rounded-lg hover:bg-muted text-muted-foreground"
            >
              <Menu size={20} />
            </button>
            <div className="hidden md:flex items-center gap-2">
              <span className="px-2 py-1 rounded-md text-[11px] font-semibold uppercase tracking-wide bg-muted text-foreground">
                {currentSection}
              </span>
              <span className="text-sm font-medium text-muted-foreground">{currentArea}</span>
            </div>
            <div className="relative hidden lg:block">
              <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
              <input
                type="text"
                placeholder="Global search (coming soon)"
                disabled
                className="w-72 pl-9 pr-4 py-1.5 text-sm border border-border rounded-lg text-muted-foreground bg-muted cursor-not-allowed"
              />
            </div>
            <button
              onClick={() => setShowCommandPalette(true)}
              className="ui-btn hidden lg:flex items-center gap-2 px-2.5 py-1.5 text-xs border border-border rounded-md text-muted-foreground hover:bg-muted"
            >
              <Command size={14} />
              Quick Actions
              <span className="text-[10px] text-muted-foreground">Ctrl/Cmd+K</span>
            </button>
          </div>

          <div className="flex items-center gap-2 sm:gap-4">
            <div className="relative" ref={notificationsMenuRef}>
              <button
                type="button"
                onClick={() => { setShowNotificationsMenu(v => !v); setShowUserMenu(false) }}
                aria-label="Notifications"
                className="ui-btn relative p-2 rounded-lg hover:bg-muted"
              >
                <Bell size={18} className="text-muted-foreground" />
                {(unreadCount?.count ?? 0) > 0 && (
                  <span className="absolute top-1 right-1 min-w-4 h-4 px-1 rounded-full bg-error text-white text-[10px] flex items-center justify-center">
                    {unreadCount.count > 9 ? '9+' : unreadCount.count}
                  </span>
                )}
              </button>
              {showNotificationsMenu && (
                <div className="absolute right-0 top-full mt-1 w-60 bg-card border border-border rounded-lg elev-raised py-1 z-50">
                  <div className="px-3 py-2 text-xs text-muted-foreground border-b border-border">
                    {unreadCount?.count ?? 0} unread notifications
                  </div>
                  <button
                    type="button"
                    onClick={() => { navigate('/i/messages'); setShowNotificationsMenu(false) }}
                    className="w-full text-left px-4 py-2 text-sm text-foreground hover:bg-muted"
                  >
                    Open inbox
                  </button>
                  <button
                    type="button"
                    onClick={() => { navigate('/i/settings?tab=notifications'); setShowNotificationsMenu(false) }}
                    className="w-full text-left px-4 py-2 text-sm text-foreground hover:bg-muted"
                  >
                    Notification settings
                  </button>
                </div>
              )}
            </div>

            <div className="relative" ref={userMenuRef}>
              <button
                type="button"
                onClick={() => { setShowUserMenu(v => !v); setShowNotificationsMenu(false) }}
                className="ui-btn flex items-center gap-2 px-2 sm:px-3 py-1.5 rounded-lg hover:bg-muted"
              >
                <div className="w-7 h-7 rounded-full bg-cobalt/10 flex items-center justify-center text-xs font-semibold text-cobalt">
                  {user?.email?.charAt(0).toUpperCase()}
                </div>
                <span className="hidden xl:inline text-sm text-muted-foreground max-w-[180px] truncate">{user?.email}</span>
              </button>
              {showUserMenu && (
                <div className="absolute right-0 top-full mt-1 w-48 bg-card border border-border rounded-lg elev-raised py-1 z-50">
                  <button
                    type="button"
                    onClick={() => { navigate('/i/settings'); setShowUserMenu(false) }}
                    className="w-full text-left px-4 py-2 text-sm text-foreground hover:bg-muted"
                  >
                    Settings
                  </button>
                  <button
                    type="button"
                    onClick={logout}
                    className="w-full text-left px-4 py-2 text-sm text-error hover:bg-error-soft/50 flex items-center gap-2"
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
        onClose={() => { setShowCommandPalette(false); setCommandQuery('') }}
        title="Quick Actions"
      >
        <div className="space-y-3">
          <Input
            value={commandQuery}
            onChange={e => setCommandQuery(e.target.value)}
            placeholder="Search action or shortcut (example: review, g r)"
            autoFocus
          />
          <div className="max-h-72 overflow-y-auto space-y-1">
            {filteredActions.length === 0 ? (
              <p className="text-sm text-muted-foreground py-3 text-center">No actions found.</p>
            ) : (
              filteredActions.map(action => (
                <button
                  key={action.id}
                  onClick={() => { action.onSelect(); setShowCommandPalette(false); setCommandQuery('') }}
                  className="w-full flex items-center justify-between px-3 py-2 text-sm rounded-md hover:bg-muted text-left"
                >
                  <span className="text-foreground">{action.label}</span>
                  <span className="text-[11px] text-muted-foreground">{action.hint}</span>
                </button>
              ))
            )}
          </div>
        </div>
      </Modal>
    </div>
  )
}
