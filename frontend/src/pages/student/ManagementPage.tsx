import { useState, lazy, Suspense, useEffect } from 'react'
import { useSearchParams, useNavigate } from 'react-router-dom'
import { FolderKanban, Calendar, MessageSquare, GraduationCap } from 'lucide-react'

// Lazy-load sub-pages
const ApplicationsPage = lazy(() => import('./ApplicationsPage'))
const CalendarPage = lazy(() => import('./CalendarPage'))
const MessagesPage = lazy(() => import('./MessagesPage'))
const WorkshopsTab = lazy(() => import('./apply/WorkshopsTab'))

type Tab = 'applications' | 'calendar' | 'messages' | 'workshops'

const TABS: { key: Tab; label: string; icon: typeof FolderKanban }[] = [
  { key: 'applications', label: 'Applications', icon: FolderKanban },
  { key: 'calendar', label: 'Calendar', icon: Calendar },
  { key: 'messages', label: 'Messages', icon: MessageSquare },
  // Phase D — Workshops moved here from Profile (feedback-only).
  { key: 'workshops', label: 'Workshops', icon: GraduationCap },
]

export default function ManagementPage() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const rawTab = searchParams.get('tab') as Tab | null
  const threadId = searchParams.get('thread')
  const [tab, setTab] = useState<Tab>(rawTab && TABS.some(t => t.key === rawTab) ? rawTab : 'applications')

  useEffect(() => {
    if (rawTab && TABS.some(t => t.key === rawTab) && rawTab !== tab) setTab(rawTab)
  }, [rawTab, tab])

  const switchTab = (t: Tab) => {
    setTab(t)
    const params = new URLSearchParams()
    if (t !== 'applications') params.set('tab', t)
    if (t === 'messages' && threadId) params.set('thread', threadId)
    const qs = params.toString()
    navigate(qs ? `/s/manage?${qs}` : '/s/manage', { replace: true })
  }

  const isInbox = tab === 'messages'

  return (
    <div className="flex min-h-0 flex-1 flex-col">
      {/* Sub-tab bar */}
      <div className="flex-shrink-0 border-b border-border bg-card px-6">
        <div className="flex gap-0.5">
          {TABS.map(t => (
            <button
              key={t.key}
              onClick={() => switchTab(t.key)}
              className={`flex items-center gap-1.5 border-b-2 px-4 py-3 text-sm font-medium transition-colors ${
                tab === t.key
                  ? 'border-secondary text-foreground'
                  : 'border-transparent text-muted-foreground hover:text-foreground'
              }`}
            >
              <t.icon size={15} />
              {t.label}
            </button>
          ))}
        </div>
      </div>

      {/* Content — inbox is a fixed two-pane surface (Spec 17 §2); other tabs scroll. */}
      <div
        className={`min-h-0 flex-1 ${isInbox ? 'overflow-hidden' : 'overflow-y-auto'}`}
      >
        <Suspense fallback={<div className="p-6 text-center text-muted-foreground">Loading...</div>}>
          {tab === 'applications' && <ApplicationsPage />}
          {tab === 'calendar' && <CalendarPage />}
          {tab === 'messages' && (
            <div className="h-full min-h-[min(100dvh-9rem,720px)] lg:min-h-[calc(100dvh-8rem)]">
              <MessagesPage initialThreadId={threadId} />
            </div>
          )}
          {tab === 'workshops' && <WorkshopsTab />}
        </Suspense>
      </div>
    </div>
  )
}
