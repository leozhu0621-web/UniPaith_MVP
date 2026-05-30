import { useEffect, useMemo, useRef, useState } from 'react'
import { Outlet, useNavigate, useLocation } from 'react-router-dom'
import { useAuthStore } from '../../stores/auth-store'
import { useUIStore } from '../../stores/ui-store'
import { showToast } from '../../stores/toast-store'
import {
  LayoutDashboard, GraduationCap, Kanban, Megaphone, MessageSquare,
  BarChart3, Settings, Bell, LogOut, Command, ChevronDown, Menu, Building2, User,
} from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import { getUnreadCount } from '../../api/notifications'
import { getInstitution, getInstitutionPrograms } from '../../api/institutions'
import Modal from '../ui/Modal'
import Input from '../ui/Input'
import Wordmark from '../ui/Wordmark'
import Dropdown from '../ui/Dropdown'
import { useDocumentTitle } from '../../hooks/useDocumentTitle'

// Top-nav surfaces — the 4 unified institution workspaces (Spec/04 §5.1, §7.2).
// Side nav is reserved for the Admissions queue only (§7.4), so everything else
// lives here. `match` lists the direct/legacy routes that belong to each surface
// so the right label stays highlighted on deep links (e.g. /i/pipeline → Admissions).
const NAV_ITEMS: { to: string; icon: typeof Kanban; label: string; match: string[] }[] = [
  { to: '/i/admissions', icon: Kanban, label: 'Admissions', match: ['/i/admissions', '/i/pipeline', '/i/interviews', '/i/inquiries', '/i/cohort-compare'] },
  { to: '/i/outreach', icon: Megaphone, label: 'Outreach', match: ['/i/outreach', '/i/campaigns', '/i/promotions', '/i/events', '/i/posts'] },
  { to: '/i/communications', icon: MessageSquare, label: 'Communications', match: ['/i/communications', '/i/templates', '/i/segments', '/i/messages'] },
  { to: '/i/programs', icon: GraduationCap, label: 'Programs', match: ['/i/programs', '/i/requirements', '/i/intake-rounds'] },
]

function matchesNav(pathname: string, prefixes: string[]) {
  return prefixes.some(p => pathname === p || pathname.startsWith(p + '/'))
}

export default function InstitutionLayout() {
  const { user, logout } = useAuthStore()
  const navigate = useNavigate()
  const location = useLocation()
  const [showCommandPalette, setShowCommandPalette] = useState(false)
  const [showNotificationsMenu, setShowNotificationsMenu] = useState(false)
  const [commandQuery, setCommandQuery] = useState('')
  const shortcutPrefixAtRef = useRef<number | null>(null)
  const notificationsMenuRef = useRef<HTMLDivElement | null>(null)
  const programSwitcherRef = useRef<HTMLDivElement | null>(null)

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

  // First-run: no institution yet → route into the setup wizard (Spec/04 §11).
  useEffect(() => {
    if (!institutionMissing) return
    if (location.pathname === '/i/setup') return
    navigate('/i/setup', { replace: true })
  }, [institutionMissing, location.pathname, navigate])

  const activeNav = NAV_ITEMS.find(item => matchesNav(location.pathname, item.match))?.to

  // Per-route page title (Spec/04 §15).
  const ip = location.pathname
  useDocumentTitle(
    activeNav === '/i/admissions' ? 'Admissions'
    : activeNav === '/i/outreach' ? 'Outreach'
    : activeNav === '/i/communications' ? 'Communications'
    : activeNav === '/i/programs' ? 'Programs'
    : ip.startsWith('/i/analytics') ? 'Analytics'
    : ip.startsWith('/i/settings') ? 'Settings'
    : ip.startsWith('/i/setup') ? 'Get started'
    : 'Dashboard',
  )

  const commandActions = useMemo(() => [
    { id: 'go-overview', label: 'Go to Dashboard', hint: 'g o', onSelect: () => navigate('/i/dashboard') },
    { id: 'go-programs', label: 'Go to Programs', hint: 'g p', onSelect: () => navigate('/i/programs') },
    { id: 'go-apps-review', label: 'Open Review Queue', hint: 'g r', onSelect: () => navigate('/i/pipeline?tab=review') },
    { id: 'go-apps-board', label: 'Open Applications Board', hint: 'g a', onSelect: () => navigate('/i/pipeline?tab=board') },
    { id: 'go-interviews', label: 'Go to Interviews', hint: 'g i', onSelect: () => navigate('/i/interviews') },
    { id: 'go-campaigns', label: 'Go to Campaigns', hint: 'g c', onSelect: () => navigate('/i/campaigns') },
    { id: 'go-events', label: 'Go to Events', hint: 'g e', onSelect: () => navigate('/i/events') },
    { id: 'go-insights', label: 'Go to Analytics', hint: 'g s', onSelect: () => navigate('/i/analytics') },
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
      if (programSwitcherRef.current && !programSwitcherRef.current.contains(target)) {
        setShowProgramList(false)
      }
    }
    document.addEventListener('mousedown', handleOutsideClick)
    return () => document.removeEventListener('mousedown', handleOutsideClick)
  }, [])

  return (
    <div className="flex flex-col h-screen bg-offwhite">
      {/* Top nav — same chrome as the student app (Spec/04 §7.2). */}
      <header className="h-16 flex items-center justify-between gap-4 px-6 border-b border-gray-200 bg-white flex-shrink-0 z-30">
        {/* Left — wordmark (home) + program scope switcher */}
        <div className="flex items-center gap-3 min-w-0">
          <button
            onClick={() => navigate('/i/dashboard')}
            className="leading-none flex-shrink-0"
            aria-label="UniPaith — dashboard"
          >
            <Wordmark className="h-6 w-auto" />
          </button>

          {programs.length > 0 && (
            <div className="relative hidden md:block" ref={programSwitcherRef}>
              <button
                onClick={() => setShowProgramList(v => !v)}
                className="flex items-center gap-1.5 max-w-[14rem] px-2.5 py-1.5 rounded-md text-sm bg-brand-slate-50 hover:bg-brand-slate-100 transition-colors"
              >
                <span className="truncate font-medium text-brand-slate-700">
                  {selectedProgramName || 'All Programs'}
                </span>
                <ChevronDown size={14} className={`text-brand-slate-400 transition-transform ${showProgramList ? 'rotate-180' : ''}`} />
              </button>
              {showProgramList && (
                <div className="absolute left-0 top-full mt-1 w-64 bg-white border border-gray-200 rounded-lg shadow-lg py-1 z-50 max-h-72 overflow-y-auto">
                  <button
                    onClick={() => { setSelectedProgram(null); setShowProgramList(false) }}
                    className={`w-full text-left px-3 py-1.5 text-sm transition-colors ${!selectedProgramId ? 'bg-brand-slate-100 text-brand-slate-800 font-medium' : 'text-gray-600 hover:bg-gray-50'}`}
                  >
                    All Programs
                  </button>
                  {programs.map((p: any) => (
                    <button
                      key={p.id}
                      onClick={() => { setSelectedProgram(p.id, p.program_name); setShowProgramList(false) }}
                      className={`w-full text-left px-3 py-1.5 text-sm flex items-center gap-1.5 transition-colors ${selectedProgramId === p.id ? 'bg-brand-slate-100 text-brand-slate-800 font-medium' : 'text-gray-600 hover:bg-gray-50'}`}
                    >
                      <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${p.is_published ? 'bg-green-400' : 'bg-gray-300'}`} />
                      <span className="truncate">{p.program_name}</span>
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Center — the four unified workspaces (collapses to a hamburger < lg) */}
        <nav className="hidden lg:flex items-center">
          {NAV_ITEMS.map(item => {
            const isActive = activeNav === item.to
            return (
              <button
                key={item.to}
                onClick={() => navigate(item.to)}
                className={`flex items-center gap-2 px-4 py-1.5 rounded-lg transition-colors relative ${
                  isActive ? 'text-cobalt' : 'text-slate hover:text-charcoal'
                }`}
              >
                <item.icon size={17} />
                <span className={`text-sm ${isActive ? 'font-semibold' : 'font-medium'}`}>{item.label}</span>
                {isActive && <span className="absolute bottom-0 left-3 right-3 h-0.5 bg-cobalt rounded-full" />}
              </button>
            )
          })}
        </nav>

        {/* Right — quick actions, notifications, account */}
        <div className="flex items-center gap-2">
          {/* Mobile hamburger — surfaces collapse here < lg (§14) */}
          <div className="lg:hidden">
            <Dropdown
              align="right"
              trigger={
                <button className="p-2 rounded-lg hover:bg-gray-100 text-gray-600" aria-label="Open navigation">
                  <Menu size={18} />
                </button>
              }
              items={[
                { label: 'Dashboard', onClick: () => navigate('/i/dashboard'), icon: <LayoutDashboard size={14} /> },
                { label: 'Admissions', onClick: () => navigate('/i/admissions'), icon: <Kanban size={14} /> },
                { label: 'Outreach', onClick: () => navigate('/i/outreach'), icon: <Megaphone size={14} /> },
                { label: 'Communications', onClick: () => navigate('/i/communications'), icon: <MessageSquare size={14} /> },
                { label: 'Programs', onClick: () => navigate('/i/programs'), icon: <GraduationCap size={14} /> },
                { label: 'Analytics', onClick: () => navigate('/i/analytics'), icon: <BarChart3 size={14} /> },
                { label: 'Settings', onClick: () => navigate('/i/settings'), icon: <Settings size={14} /> },
              ]}
            />
          </div>

          <button
            onClick={() => setShowCommandPalette(true)}
            className="hidden lg:flex items-center gap-2 px-2.5 py-1.5 text-xs border border-gray-200 rounded-md text-gray-600 hover:bg-gray-50"
          >
            <Command size={14} />
            Quick Actions
            <span className="text-[10px] text-gray-400">⌘K</span>
          </button>

          <div className="relative" ref={notificationsMenuRef}>
            <button
              type="button"
              onClick={() => setShowNotificationsMenu(v => !v)}
              className="relative p-2 rounded-lg hover:bg-gray-100"
              aria-label="Notifications"
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
                  onClick={() => { navigate('/i/messages'); setShowNotificationsMenu(false) }}
                  className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
                >
                  Open inbox
                </button>
                <button
                  type="button"
                  onClick={() => { navigate('/i/settings?tab=notifications'); setShowNotificationsMenu(false) }}
                  className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
                >
                  Notification settings
                </button>
              </div>
            )}
          </div>

          <Dropdown
            align="right"
            trigger={
              <button className="flex items-center gap-2 px-2 py-1.5 rounded-lg hover:bg-gray-100" aria-label="Account menu">
                <div className="w-7 h-7 rounded-full bg-brand-slate-100 flex items-center justify-center text-xs font-medium text-brand-slate-700">
                  {user?.email?.charAt(0).toUpperCase()}
                </div>
                <span className="hidden xl:inline text-sm text-gray-700 max-w-[12rem] truncate">{user?.email}</span>
              </button>
            }
            items={[
              { label: 'Institution settings', onClick: () => navigate('/i/settings'), icon: <Settings size={14} /> },
              { label: 'Switch institution', onClick: () => showToast('Multi-institution switching is coming soon.', 'info'), icon: <Building2 size={14} /> },
              { label: 'Account', onClick: () => navigate('/i/settings?tab=account'), icon: <User size={14} /> },
              { label: 'Sign out', onClick: logout, icon: <LogOut size={14} />, variant: 'danger' },
            ]}
          />
        </div>
      </header>

      <main className="flex-1 overflow-y-auto">
        <Outlet />
      </main>

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
          />
          <div className="max-h-72 overflow-y-auto space-y-1">
            {filteredActions.length === 0 ? (
              <p className="text-sm text-gray-500 py-3 text-center">No actions found.</p>
            ) : (
              filteredActions.map(action => (
                <button
                  key={action.id}
                  onClick={() => { action.onSelect(); setShowCommandPalette(false); setCommandQuery('') }}
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
