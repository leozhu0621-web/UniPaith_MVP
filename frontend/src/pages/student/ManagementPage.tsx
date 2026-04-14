import { useState, lazy, Suspense } from 'react'
import { useSearchParams, useNavigate } from 'react-router-dom'
import { FolderKanban, Calendar, MessageSquare } from 'lucide-react'

// Lazy-load sub-pages
const ApplicationsPage = lazy(() => import('./ApplicationsPage'))
const CalendarPage = lazy(() => import('./CalendarPage'))
const MessagesPage = lazy(() => import('./MessagesPage'))

type Tab = 'applications' | 'calendar' | 'messages'

const TABS: { key: Tab; label: string; icon: typeof FolderKanban }[] = [
  { key: 'applications', label: 'Applications', icon: FolderKanban },
  { key: 'calendar', label: 'Calendar', icon: Calendar },
  { key: 'messages', label: 'Messages', icon: MessageSquare },
]

export default function ManagementPage() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const rawTab = searchParams.get('tab') as Tab | null
  const [tab, setTab] = useState<Tab>(rawTab && TABS.some(t => t.key === rawTab) ? rawTab : 'applications')

  const switchTab = (t: Tab) => {
    setTab(t)
    navigate(t === 'applications' ? '/s/manage' : `/s/manage?tab=${t}`, { replace: true })
  }

  return (
    <div className="flex flex-col h-full">
      {/* Sub-tab bar */}
      <div className="bg-white border-b border-divider px-6 flex-shrink-0">
        <div className="flex gap-0.5">
          {TABS.map(t => (
            <button
              key={t.key}
              onClick={() => switchTab(t.key)}
              className={`flex items-center gap-1.5 px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
                tab === t.key
                  ? 'border-student text-student'
                  : 'border-transparent text-student-text hover:text-student-ink'
              }`}
            >
              <t.icon size={15} />
              {t.label}
            </button>
          ))}
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto">
        <Suspense fallback={<div className="p-6 text-center text-student-text">Loading...</div>}>
          {tab === 'applications' && <ApplicationsPage />}
          {tab === 'calendar' && <CalendarPage />}
          {tab === 'messages' && <MessagesPage />}
        </Suspense>
      </div>
    </div>
  )
}
