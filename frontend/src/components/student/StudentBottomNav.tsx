// StudentBottomNav — Spec/02b-design-system-mobile.md §3.1.
// Fixed bottom tab bar at base–md (thumb-reachable). 56px tall, no gold
// in the chrome. Avatar tab opens a sheet (Profile / Saved / Settings /
// Sign out). Active tab uses cobalt icon + label; inactive uses muted.

import { useState } from 'react'
import { NavLink, useNavigate } from 'react-router-dom'
import {
  Compass, Target, FolderKanban, Newspaper,
  User, Bookmark, Settings, LogOut,
} from 'lucide-react'
import clsx from 'clsx'
import { useAuthStore } from '../../stores/auth-store'
import BottomSheet from '../ui/BottomSheet'
import Avatar from '../ui/Avatar'

type TabDef = {
  to: string
  icon: typeof Compass
  label: string
  end?: boolean
}

const TABS: TabDef[] = [
  { to: '/s', icon: Compass, label: 'Discover', end: true },
  { to: '/s/explore', icon: Target, label: 'Match' },
  { to: '/s/manage', icon: FolderKanban, label: 'Apply' },
  { to: '/s/posts', icon: Newspaper, label: 'Connect' },
]

export default function StudentBottomNav() {
  const navigate = useNavigate()
  const { user, logout } = useAuthStore()
  const [sheetOpen, setSheetOpen] = useState(false)

  return (
    <>
      <nav
        className="fixed bottom-0 inset-x-0 z-40 h-14 lg:hidden bg-card border-t border-border pb-safe motion-base"
        aria-label="Student stages"
      >
        <ul className="flex h-full items-stretch justify-around px-1">
          {TABS.map(tab => (
            <li key={tab.to} className="flex-1">
              <NavLink
                to={tab.to}
                end={tab.end}
                className={({ isActive }) =>
                  clsx(
                    'flex flex-col items-center justify-center gap-0.5 h-full px-1 motion-fast transition-colors',
                    'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#FFD60A] rounded-md',
                    'min-h-[44px]',
                    isActive
                      ? 'text-[#2A6BD4] dark:text-[#6FA0E8]'
                      : 'text-muted-foreground hover:text-foreground',
                  )
                }
              >
                <tab.icon size={20} aria-hidden />
                <span className="text-[10px] font-bold leading-none">{tab.label}</span>
              </NavLink>
            </li>
          ))}
          <li className="flex-1">
            <button
              type="button"
              onClick={() => setSheetOpen(true)}
              aria-label="Account menu"
              className="flex flex-col items-center justify-center gap-0.5 h-full w-full px-1 text-muted-foreground hover:text-foreground motion-fast transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#FFD60A] rounded-md min-h-[44px]"
            >
              <Avatar name={user?.email || '?'} size="sm" />
              <span className="text-[10px] font-bold leading-none">Account</span>
            </button>
          </li>
        </ul>
      </nav>

      <BottomSheet isOpen={sheetOpen} onClose={() => setSheetOpen(false)} title={user?.email || 'Account'}>
        <div className="flex flex-col gap-1">
          <SheetItem
            icon={<User size={18} />}
            label="My profile"
            onClick={() => {
              setSheetOpen(false)
              navigate('/s/profile')
            }}
          />
          <SheetItem
            icon={<Bookmark size={18} />}
            label="Saved"
            onClick={() => {
              setSheetOpen(false)
              navigate('/s/saved')
            }}
          />
          <SheetItem
            icon={<Settings size={18} />}
            label="Settings"
            onClick={() => {
              setSheetOpen(false)
              navigate('/s/settings')
            }}
          />
          <div className="h-px bg-border my-2" />
          <SheetItem
            icon={<LogOut size={18} />}
            label="Sign out"
            destructive
            onClick={() => {
              setSheetOpen(false)
              logout()
            }}
          />
        </div>
      </BottomSheet>
    </>
  )
}

function SheetItem({
  icon,
  label,
  onClick,
  destructive,
}: {
  icon: React.ReactNode
  label: string
  onClick: () => void
  destructive?: boolean
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={clsx(
        'flex items-center gap-3 px-2 py-3 rounded-lg motion-fast transition-colors min-h-[44px]',
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#FFD60A]',
        destructive
          ? 'text-[#B5321F] hover:bg-[#F2D7D0]/40 dark:text-[#FF8470] dark:hover:bg-[#3D1E1A]/40'
          : 'text-foreground hover:bg-muted',
      )}
    >
      {icon}
      <span className="text-base font-bold">{label}</span>
    </button>
  )
}
