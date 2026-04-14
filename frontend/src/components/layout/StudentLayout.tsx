import { Outlet, NavLink, useNavigate, useLocation } from 'react-router-dom'
import { useAuthStore } from '../../stores/auth-store'
import { useCounselorStore } from '../../stores/counselor-store'
import MiniCounselorPanel from '../student/MiniCounselorPanel'
import {
  Sparkles, Newspaper, Search, FolderKanban,
  Bell, LogOut, User, Bookmark, Settings, MessageSquare,
} from 'lucide-react'
import Avatar from '../ui/Avatar'
import Dropdown from '../ui/Dropdown'
import CompareTray from '../student/CompareTray'

export default function StudentLayout() {
  const { user, logout } = useAuthStore()
  const navigate = useNavigate()
  const location = useLocation()
  const { isMinimized, setMinimized } = useCounselorStore()

  const isCounselorTab = location.pathname === '/s' || location.pathname === '/s/'
  const isOtherTab = !isCounselorTab
  const showMiniCounselor = isOtherTab && !isMinimized

  return (
    <div className="flex flex-col h-screen bg-offwhite">
      {/* Top bar */}
      <header className="h-14 flex items-center justify-between px-6 bg-white border-b border-divider flex-shrink-0 z-30">
        <NavLink to="/s" className="text-lg font-bold tracking-tight">
          <span className="text-student">Uni</span><span className="text-student-ink font-extrabold">Paith</span>
        </NavLink>

        {/* Nav with thin divider after Counselor */}
        <nav className="flex items-center">
          {/* Counselor — separated */}
          <NavLink
            to="/s"
            end
            className={({ isActive }) =>
              `flex flex-col items-center px-4 py-1.5 rounded-lg transition-colors relative ${
                isActive ? 'text-student' : 'text-slate hover:text-student-ink'
              }`
            }
          >
            {({ isActive }) => (
              <>
                <Sparkles size={19} />
                <span className="text-[10px] mt-0.5 font-medium">Counselor</span>
                {isActive && <span className="absolute bottom-0 left-2 right-2 h-0.5 bg-student rounded-full" />}
              </>
            )}
          </NavLink>

          {/* Thin divider line */}
          <div className="w-px h-8 bg-divider mx-1" />

          {/* Other tabs */}
          {[
            { to: '/s/posts', icon: Newspaper, label: 'Posts' },
            { to: '/s/explore', icon: Search, label: 'Explore' },
            { to: '/s/manage', icon: FolderKanban, label: 'Management' },
          ].map(item => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `flex flex-col items-center px-4 py-1.5 rounded-lg transition-colors relative ${
                  isActive ? 'text-student' : 'text-slate hover:text-student-ink'
                }`
              }
            >
              {({ isActive }) => (
                <>
                  <item.icon size={19} />
                  <span className="text-[10px] mt-0.5 font-medium">{item.label}</span>
                  {isActive && <span className="absolute bottom-0 left-2 right-2 h-0.5 bg-student rounded-full" />}
                </>
              )}
            </NavLink>
          ))}
        </nav>

        <div className="flex items-center gap-2">
          <button
            onClick={() => navigate('/s/manage?tab=messages')}
            className="relative p-2 rounded-lg hover:bg-student-mist text-slate hover:text-student-ink transition-colors"
          >
            <Bell size={19} />
          </button>

          <Dropdown
            trigger={
              <button className="p-1 rounded-lg hover:bg-student-mist transition-colors">
                <Avatar name={user?.email || '?'} size="sm" />
              </button>
            }
            items={[
              { label: 'My Profile', onClick: () => navigate('/s/profile'), icon: <User size={14} /> },
              { label: 'Saved', onClick: () => navigate('/s/saved'), icon: <Bookmark size={14} /> },
              { label: 'Settings', onClick: () => navigate('/s/settings'), icon: <Settings size={14} /> },
              { label: 'Sign out', onClick: logout, icon: <LogOut size={14} />, variant: 'danger' },
            ]}
          />
        </div>
      </header>

      {/* Body with sliding panels */}
      <div className="flex-1 flex overflow-hidden relative">
        {/* Mini counselor panel — slides in/out on non-counselor tabs */}
        <div
          className={`flex-shrink-0 overflow-hidden transition-all duration-300 ease-in-out ${
            showMiniCounselor ? 'w-72 opacity-100' : 'w-0 opacity-0'
          }`}
        >
          <div className="w-72 h-full">
            <MiniCounselorPanel />
          </div>
        </div>

        {/* Show counselor toggle button when minimized on other tabs */}
        {isOtherTab && isMinimized && (
          <button
            onClick={() => setMinimized(false)}
            className="absolute left-0 top-3 z-20 flex items-center gap-1 pl-1.5 pr-3 py-2 bg-white border border-divider border-l-0 rounded-r-xl shadow-sm text-student hover:bg-student-mist transition-all duration-200 animate-slide-in-left"
            title="Show counselor"
          >
            <MessageSquare size={14} />
            <span className="text-[10px] font-medium">Chat</span>
          </button>
        )}

        {/* Main content area with page transition */}
        <main className="flex-1 overflow-y-auto transition-all duration-300 ease-in-out">
          <div key={location.pathname} className="animate-page-in h-full">
            <Outlet />
          </div>
        </main>
      </div>
      <CompareTray />
    </div>
  )
}
