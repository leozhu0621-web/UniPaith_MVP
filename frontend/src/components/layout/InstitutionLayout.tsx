import { useEffect, useState } from 'react'
import SkipLink from './SkipLink'
import { Outlet, NavLink, useNavigate, useLocation } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { useAuthStore } from '../../stores/auth-store'
import { useUIStore } from '../../stores/ui-store'
import { getInstitutionPrograms, getSetupState } from '../../api/institutions'
import Wordmark from '../ui/Wordmark'
import Dropdown from '../ui/Dropdown'
import Sheet from '../ui/Sheet'
import NotificationBell from '../notifications/NotificationBell'
import {
  LogOut, Settings, Menu, ChevronDown, ScrollText,
} from 'lucide-react'

const TOP_NAV = [
  { to: '/i/dashboard', label: 'Dashboard' },
  { to: '/i/recruitment', label: 'Recruitment' },
  { to: '/i/admissions', label: 'Admissions' },
  { to: '/i/outreach', label: 'Outreach' },
  { to: '/i/communications', label: 'Communications' },
  { to: '/i/programs', label: 'Programs' },
  { to: '/i/analytics', label: 'Analytics' },
]

export default function InstitutionLayout() {
  const { user, logout } = useAuthStore()
  const navigate = useNavigate()
  const location = useLocation()
  const [mobileNavOpen, setMobileNavOpen] = useState(false)
  const [showProgramList, setShowProgramList] = useState(false)
  const { selectedProgramId, selectedProgramName, setSelectedProgram } = useUIStore()

  // Spec 30 §2/§4 — first-run gating. While setup is incomplete the institution
  // is forced to /i/setup (and /i/data for step 3 upload) and the rest of the nav is dimmed.
  const setupQ = useQuery({ queryKey: ['institution-setup'], queryFn: getSetupState })
  const setupIncomplete = setupQ.isSuccess && setupQ.data?.setup_complete !== true
  const programsQ = useQuery({
    queryKey: ['institution-programs'],
    queryFn: getInstitutionPrograms,
    retry: false,
    enabled:
      setupQ.isSuccess &&
      (!!setupQ.data?.setup_complete || !!setupQ.data?.steps_complete?.program),
  })
  const programs = Array.isArray(programsQ.data) ? programsQ.data : []
  const setupExemptPaths = ['/i/setup', '/i/data']

  useEffect(() => {
    if (!setupIncomplete) return
    if (setupExemptPaths.some(p => location.pathname === p || location.pathname.startsWith(`${p}/`))) return
    navigate('/i/setup', { replace: true })
  }, [setupIncomplete, location.pathname, navigate])

  useEffect(() => {
    setMobileNavOpen(false)
  }, [location.pathname])

  const showSetup = setupIncomplete

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
            className={`w-full text-left px-2 py-1 rounded text-xs transition-colors ${!selectedProgramId ? 'bg-secondary/10 text-secondary font-medium' : 'text-muted-foreground hover:bg-muted'}`}
          >
            All Programs
          </button>
          {programs.map((p: { id: string; program_name: string; is_published?: boolean }) => (
            <button
              key={p.id}
              onClick={() => { setSelectedProgram(p.id, p.program_name); setShowProgramList(false) }}
              className={`w-full text-left px-2 py-1 rounded text-xs flex items-center gap-1.5 transition-colors ${selectedProgramId === p.id ? 'bg-secondary/10 text-secondary font-medium' : 'text-muted-foreground hover:bg-muted'}`}
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
    ...(showSetup ? [{ to: '/i/setup', label: 'Continue setup' }] : []),
    ...TOP_NAV,
    { to: '/i/audit-log', label: 'Audit log' },
    { to: '/i/settings', label: 'Settings' },
  ]

  return (
    <div className="flex flex-col h-screen bg-background">
      <SkipLink />
      <header className="hidden lg:flex h-16 items-center justify-between px-8 bg-background border-b border-border flex-shrink-0 z-30">
        <NavLink to="/i/dashboard" className="leading-none" aria-label="Institution home">
          <Wordmark className="h-7 w-auto" />
        </NavLink>
        <nav
          className={`flex items-center gap-1 transition-opacity ${setupIncomplete ? 'pointer-events-none select-none opacity-40' : ''}`}
          aria-label="Primary"
          aria-hidden={setupIncomplete || undefined}
        >
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
          <NotificationBell />
          <Dropdown
            trigger={
              <button aria-label="Account menu" className="ui-btn p-1 rounded-lg hover:bg-muted transition-colors">
                <div className="w-8 h-8 rounded-full bg-secondary/10 flex items-center justify-center text-xs font-semibold text-secondary">
                  {user?.email?.charAt(0).toUpperCase()}
                </div>
              </button>
            }
            items={[
              { label: 'Institution settings', onClick: () => navigate('/i/settings'), icon: <Settings size={14} /> },
              { label: 'Audit log', onClick: () => navigate('/i/audit-log'), icon: <ScrollText size={14} /> },
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
        <NotificationBell />
      </header>

      <Sheet isOpen={mobileNavOpen} onClose={() => setMobileNavOpen(false)} side="right" title="Menu">
        <div className="px-4 pb-2 border-b border-border mb-2">
          <Wordmark className="h-6 w-auto" />
        </div>
        {programSwitcher}
        <nav className="flex flex-col py-2">
          {mobileLinks.map(item => {
            const dimmed = setupIncomplete && item.to !== '/i/setup'
            return (
              <NavLink
                key={item.to}
                to={item.to}
                onClick={(e) => {
                  if (dimmed) {
                    e.preventDefault()
                    return
                  }
                  setMobileNavOpen(false)
                }}
                aria-disabled={dimmed || undefined}
                className={({ isActive }) =>
                  `touch-target px-4 py-3 text-sm rounded-md mx-2 transition-colors ${
                    dimmed
                      ? 'pointer-events-none opacity-40'
                      : isActive
                        ? 'bg-secondary/10 text-secondary font-medium'
                        : 'text-foreground hover:bg-muted'
                  }`
                }
              >
                {item.label}
              </NavLink>
            )
          })}
          <button
            onClick={() => { setMobileNavOpen(false); logout() }}
            className="touch-target mx-2 mt-2 px-4 py-3 text-sm text-error hover:bg-error-soft/50 rounded-md text-left flex items-center gap-2"
          >
            <LogOut size={16} /> Sign out
          </button>
        </nav>
      </Sheet>

      <main id="main" tabIndex={-1} className="flex-1 overflow-y-auto outline-none">
        <Outlet />
      </main>
    </div>
  )
}
