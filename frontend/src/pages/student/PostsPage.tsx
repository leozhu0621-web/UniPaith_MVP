// Connect — Student Stage 3a (Spec 20). The consumption mirror of the
// institution Outreach module: Updates · Events · Peers, scoped to the
// institutions the student follows. Lives at /s/posts, labeled "Connect".
import { useSearchParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { useRef, useState } from 'react'
import { Calendar, ChevronDown, Newspaper, Users } from 'lucide-react'
import { getFollowing } from '../../api/connect'
import UpdatesTab from './connect/UpdatesTab'
import EventsTab from './connect/EventsTab'
import PeersTab from './connect/PeersTab'
import ManageFollowingPanel from './connect/ManageFollowingPanel'
import PageHeader from '../../components/student/density/PageHeader'

type ConnectTab = 'updates' | 'events' | 'peers'

const TABS: { key: ConnectTab; label: string; icon: typeof Newspaper }[] = [
  { key: 'updates', label: 'Updates', icon: Newspaper },
  { key: 'events', label: 'Events', icon: Calendar },
  { key: 'peers', label: 'Peers', icon: Users },
]

export default function PostsPage() {
  const [params, setParams] = useSearchParams()
  const [managing, setManaging] = useState(false)
  const tablistRef = useRef<HTMLDivElement>(null)

  const urlTab = params.get('tab') as ConnectTab | null
  const tab: ConnectTab = TABS.some(t => t.key === urlTab) ? (urlTab as ConnectTab) : 'updates'
  const setTab = (t: ConnectTab) => setParams(prev => {
    const next = new URLSearchParams(prev)
    next.set('tab', t)
    return next
  }, { replace: true })

  const { data: follows } = useQuery({ queryKey: ['connect-follows'], queryFn: getFollowing, retry: false })
  const followCount = follows?.length ?? 0

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
      setTab(TABS[next].key)
    }
  }

  return (
    <div className="h-full overflow-y-auto">
      <div className="max-w-5xl w-full mx-auto px-6 py-6">
        {/* Header (Spec 20 §3; eyebrow = surface name, Spec 2026-06-10 §3) */}
        <PageHeader
          eyebrow="Connect"
          title="Updates, events, and peers"
          sub="From the institutions you follow"
        />

        {/* Tabs + Manage following */}
        <div className="flex items-end justify-between border-b border-border mb-5">
          <div ref={tablistRef} role="tablist" aria-label="Connect sections" className="flex gap-1">
            {TABS.map((t, idx) => (
              <button
                key={t.key}
                id={`connect-tab-${t.key}`}
                role="tab"
                aria-selected={tab === t.key}
                aria-controls={`connect-panel-${t.key}`}
                tabIndex={tab === t.key ? 0 : -1}
                onClick={() => setTab(t.key)}
                onKeyDown={e => handleTabKeyDown(e, idx)}
                className={`flex items-center gap-1.5 px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors ${
                  tab === t.key
                    ? 'border-secondary text-secondary'
                    : 'border-transparent text-muted-foreground hover:text-foreground'
                }`}
              >
                <t.icon size={14} />
                {t.label}
              </button>
            ))}
          </div>
          <button
            onClick={() => setManaging(true)}
            className="inline-flex sm:hidden items-center gap-1 px-3 py-1.5 mb-1 text-xs font-medium text-muted-foreground hover:text-foreground rounded-lg hover:bg-muted transition-colors"
          >
            Following ({followCount}) <ChevronDown size={13} />
          </button>
          <button
            onClick={() => setManaging(true)}
            className="hidden sm:inline-flex items-center gap-1 px-3 py-1.5 mb-1 text-xs font-medium text-muted-foreground hover:text-foreground rounded-lg hover:bg-muted transition-colors"
          >
            Manage following ({followCount}) <ChevronDown size={13} />
          </button>
        </div>

        <div
          id={`connect-panel-${tab}`}
          role="tabpanel"
          aria-labelledby={`connect-tab-${tab}`}
          tabIndex={0}
          className="focus-visible:outline-none"
        >
          {tab === 'updates' && <UpdatesTab />}
          {tab === 'events' && <EventsTab />}
          {tab === 'peers' && <PeersTab />}
        </div>
      </div>

      {managing && <ManageFollowingPanel onClose={() => setManaging(false)} />}
    </div>
  )
}
