import { useEffect, useState } from 'react'
import { Outlet, NavLink, useNavigate, useLocation } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { useAuthStore } from '../../stores/auth-store'
import { useUIStore } from '../../stores/ui-store'
import { getUnreadCount } from '../../api/notifications'
import { getInstitution, getInstitutionPrograms, getInstitutionSetup } from '../../api/institutions'
import Wordmark from '../ui/Wordmark'
import Dropdown from '../ui/Dropdown'
import Sheet from '../ui/Sheet'
import {
  Bell, LogOut, Settings, Menu, ChevronDown,
} from 'lucide-react'

const TOP_NAV = [
  { to: '/i/admissions', label: 'Admissions' },
  { to: '/i/outreach', label: 'Outreach' },
  { to: '/i/communications', label: 'Communications' },
  { to: '/i/programs', label: 'Programs' },
]

export default function InstitutionLayout() {
  const { user, logout } = useAuthStore()
  const navigate = useNavigate()
  const location = useLocation()
  const [mobileNavOpen, setMobileNavOpen] = useState(false)
  const [showProgramList, setShowProgramList] = useState(false)
  const { selectedProgramId, selectedProgramName, setSelectedProgram } = useUIStore()

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
  const setupQ = useQuery({
    queryKey: ['institution-setup'],
    queryFn: getInstitutionSetup,
  })
  const programsQ = useQuery({
    queryKey: ['institution-programs'],
    queryFn: getInstitutionPrograms,
    enabled: !!institutionQ.data,
  })
  const programs = Array.isArray(programsQ.data) ? programsQ.data : []
  const institutionMissing =
    institutionQ.isError &&
    institutionQ.error instanceof Error &&
    /not found|no institution|404/i.test(institutionQ.error.message)
  const setupIncomplete = setupQ.data != null && !setupQ.data.setup_complete

  const setupAllowedPaths = ['/i/setup', '/i/data']

  useEffect(() => {
    if (setupQ.isLoading) return
    const needsSetup = institutionMissing || setupIncomplete
    if (!needsSetup) return
    if (setupAllowedPaths.some(p => location.pathname === p || location.pathname.startsWith(`${p}/`))) return
    navigate('/i/setup', { replace: true })
  }, [institutionMissing, setupIncomplete, setupQ.isLoading, location.pathname, navigate])

  useEffect(() => {
    setMobileNavOpen(false)
  }, [location.pathname])

  const showSetup = institutionMissing || setupIncomplete
  const navDimmed = setupIncomplete && !institutionMissing

  const programSwitcher = (
    <div className="px-4 py-3 border-b border-border">
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
          {programs.map((p: { id: string; program_name: string; is_published?: boolean }) => (
            <button
              key={p.id}
              onClick={() => { setSelectedProgram(p.id, p.program_name); setShowProgramList(false) }}
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

  const mobileLinks = [
    { to: '/i/dashboard', label: 'Dashboard', dimmed: navDimmed },
    ...(showSetup ? [{ to: '/i/setup', label: 'Set up', dimmed: false }] : []),
    ...TOP_NAV.map(item => ({ ...item, dimmed: navDimmed })),
    { to: '/i/analytics', label: 'Analytics', dimmed: navDimmed },
    { to: '/i/settings', label: 'Settings', dimmed: navDimmed },
  ]

  return (
    <div className="flex flex-col h-screen bg-background">
      <header className="hidden lg:flex h-16 items-center justify-between px-8 bg-background border-b border-border flex-shrink-0 z-30">
        <NavLink to="/i/dashboard" className="leading-none" aria-label="Institution home">
          <Wordmark className="h-7 w-auto" />
        </NavLink>
        <nav className={`flex items-center gap-1 ${navDimmed ? 'opacity-40 pointer-events-none' : ''}`} aria-label="Primary">
          {TOP_NAV.map(item => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `ui-btn relative px-4 h-16 inline-flex items-center text-sm transition-colors ${
                  isActive ? 'text-foreground font-semibold' : 'text-muted-foreground hover:text-foreground font-medium'
                }`
              }
            >
              {({ isActive }) => (
                <>
                  {item.label}
                  {isActive && <span className="absolute bottom-0 left-3 right-3 h-0.5 bg-primary" />}
                </>
              )}
            </NavLink>
          ))}
        </nav>
        <div className="flex items-center gap-2">
          <button
            onClick={() => navigate('/i/messages')}
            aria-label="Notifications"
            className="ui-btn relative p-2 rounded-lg hover:bg-muted text-muted-foreground hover:text-foreground transition-colors"
          >
            <Bell size={19} />
            {(unreadCount?.count ?? 0) > 0 && (
              <span className="absolute top-1 right-1 min-w-4 h-4 px-1 rounded-full bg-error text-white text-[10px] flex items-center justify-center">
                {unreadCount!.count > 9 ? '9+' : unreadCount!.count}
              </span>
            )}
          </button>
          <Dropdown
            trigger={
              <button aria-label="Account menu" className="ui-btn p-1 rounded-lg hover:bg-muted transition-colors">
                <div className="w-8 h-8 rounded-full bg-cobalt/10 flex items-center justify-center text-xs font-semibold text-cobalt">
                  {user?.email?.charAt(0).toUpperCase()}
                </div>
              </button>
            }
            items={[
              { label: 'Institution settings', onClick: () => navigate('/i/settings'), icon: <Settings size={14} /> },
              { label: 'Sign out', onClick: logout, icon: <LogOut size={14} />, variant: 'danger' },
            ]}
          />
        </div>
      </header>

      <header className="flex lg:hidden h-14 items-center justify-between px-4 bg-background border-b border-border flex-shrink-0 z-30">
        <button onClick={() => setMobileNavOpen(true)} aria-label="Open menu" className="ui-btn p-2 -ml-1 rounded-lg hover:bg-muted text-muted-foreground">
          <Menu size={20} />
        </button>
        <NavLink to="/i/dashboard" aria-label="Institution home" className="leading-none">
          <img src="/favicon.svg" alt="UniPaith" className="h-9 w-9 rounded-md" />
        </NavLink>
        <button onClick={() => navigate('/i/messages')} aria-label="Notifications" className="ui-btn relative p-2 rounded-lg hover:bg-muted text-muted-foreground">
          <Bell size={20} />
        </button>
      </header>

      <Sheet isOpen={mobileNavOpen} onClose={() => setMobileNavOpen(false)} side="right" title="Menu">
        <div className="px-4 pb-2 border-b border-border mb-2">
          <Wordmark className="h-6 w-auto" />
        </div>
        {programSwitcher}
        <nav className="flex flex-col py-2">
          {mobileLinks.map(item => (
            <NavLink
              key={item.to}
              to={item.to}
              onClick={() => setMobileNavOpen(false)}
              className={({ isActive }) =>
                `touch-target px-4 py-3 text-sm rounded-md mx-2 transition-colors ${
                  item.dimmed ? 'opacity-40 pointer-events-none' : ''
                } ${
                  isActive ? 'bg-cobalt/10 text-cobalt font-medium' : 'text-foreground hover:bg-muted'
                }`
              }
            >
              {item.label}
            </NavLink>
          ))}
          <button
            onClick={() => { setMobileNavOpen(false); logout() }}
            className="touch-target mx-2 mt-2 px-4 py-3 text-sm text-error hover:bg-error-soft/50 rounded-md text-left flex items-center gap-2"
          >
            <LogOut size={16} /> Sign out
          </button>
        </nav>
      </Sheet>

      <main className="flex-1 overflow-y-auto">
        <Outlet />
      </main>
    </div>
  )
}
