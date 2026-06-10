import { useState, lazy, Suspense, useEffect, useRef } from 'react'
import { useSearchParams, useNavigate } from 'react-router-dom'
import {
  FolderKanban,
  Calendar,
  MessageSquare,
  GraduationCap,
  NotebookPen,
} from 'lucide-react'

// Lazy-load sub-pages
const ApplicationsPage = lazy(() => import('./ApplicationsPage'))
const CalendarPage = lazy(() => import('./CalendarPage'))
const MessagesPage = lazy(() => import('./MessagesPage'))
const PromptLibraryTab = lazy(() => import('./apply/promptlibrary/PromptLibraryTab'))
const WorkshopsTab = lazy(() => import('./apply/WorkshopsTab'))

type Tab = 'applications' | 'calendar' | 'messages' | 'prompts' | 'workshops'

const TABS: { key: Tab; label: string; icon: typeof FolderKanban }[] = [
  { key: 'applications', label: 'Applications', icon: FolderKanban },
  { key: 'calendar', label: 'Calendar', icon: Calendar },
  { key: 'messages', label: 'Messages', icon: MessageSquare },
  // Spec 42 — Prompt Library (behavioral practice + story bank), before
  // Workshops (which give feedback on a finished draft).
  { key: 'prompts', label: 'Prompts', icon: NotebookPen },
  // Phase D — Workshops moved here from Profile (feedback-only).
  { key: 'workshops', label: 'Workshops', icon: GraduationCap },
]

export default function ManagementPage() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const tablistRef = useRef<HTMLDivElement>(null)
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

  // Arrow-key / Home / End keyboard navigation on the tablist (ARIA tabs pattern).
  const handleTabKeyDown = (e: React.KeyboardEvent<HTMLButtonElement>, idx: number) => {
    const buttons = tablistRef.current?.querySelectorAll<HTMLButtonElement>('[role="tab"]')
    if (!buttons) return
    let next = -1
    if (e.key === 'ArrowRight') next = (idx + 1) % buttons.length
    else if (e.key === 'ArrowLeft') next = (idx - 1 + buttons.length) % buttons.length
    else if (e.key === 'Home') next = 0
    else if (e.key === 'End') next = buttons.length - 1
    if (next >= 0) {
      e.preventDefault()
      buttons[next].focus()
      switchTab(TABS[next].key)
    }
  }

  const isInbox = tab === 'messages'

  return (
    <div className="flex min-h-0 flex-1 flex-col">
      {/* Sub-tab bar */}
      <div className="flex-shrink-0 border-b border-border bg-card px-6">
        <div ref={tablistRef} role="tablist" aria-label="Apply sections" className="flex gap-0.5">
          {TABS.map((t, idx) => (
            <button
              key={t.key}
              id={`manage-tab-${t.key}`}
              role="tab"
              aria-selected={tab === t.key}
              aria-controls={`manage-panel-${t.key}`}
              tabIndex={tab === t.key ? 0 : -1}
              onClick={() => switchTab(t.key)}
              onKeyDown={e => handleTabKeyDown(e, idx)}
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
        id={`manage-panel-${tab}`}
        role="tabpanel"
        aria-labelledby={`manage-tab-${tab}`}
        tabIndex={0}
        className={`min-h-0 flex-1 focus-visible:outline-none ${isInbox ? 'overflow-hidden' : 'overflow-y-auto'}`}
      >
        <Suspense fallback={<div className="p-6 text-center text-muted-foreground">Loading...</div>}>
          {tab === 'applications' && <ApplicationsPage />}
          {tab === 'calendar' && <CalendarPage />}
          {tab === 'messages' && (
            <div className="h-full min-h-[min(100dvh-9rem,720px)] lg:min-h-[calc(100dvh-8rem)]">
              <MessagesPage initialThreadId={threadId} />
            </div>
          )}
          {tab === 'prompts' && <PromptLibraryTab />}
          {tab === 'workshops' && <WorkshopsTab />}
        </Suspense>
      </div>
    </div>
  )
}
