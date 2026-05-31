// Connect — Student Stage 3a (Spec 20). The consumption mirror of the
// institution Outreach module: Updates · Events · Peers, scoped to the
// institutions the student follows. Lives at /s/posts, labeled "Connect".
import { useSearchParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { Calendar, ChevronDown, Newspaper, Users } from 'lucide-react'
import { getFollowing } from '../../api/connect'
import UpdatesTab from './connect/UpdatesTab'
import EventsTab from './connect/EventsTab'
import PeersTab from './connect/PeersTab'
import ManageFollowingPanel from './connect/ManageFollowingPanel'

type ConnectTab = 'updates' | 'events' | 'peers'

const TABS: { key: ConnectTab; label: string; icon: typeof Newspaper }[] = [
  { key: 'updates', label: 'Updates', icon: Newspaper },
  { key: 'events', label: 'Events', icon: Calendar },
  { key: 'peers', label: 'Peers', icon: Users },
]

export default function PostsPage() {
  const [params, setParams] = useSearchParams()
  const [managing, setManaging] = useState(false)

  const urlTab = params.get('tab') as ConnectTab | null
  const tab: ConnectTab = TABS.some(t => t.key === urlTab) ? (urlTab as ConnectTab) : 'updates'
  const setTab = (t: ConnectTab) => setParams(prev => {
    const next = new URLSearchParams(prev)
    next.set('tab', t)
    return next
  }, { replace: true })

  const { data: follows } = useQuery({ queryKey: ['connect-follows'], queryFn: getFollowing, retry: false })
  const followCount = follows?.length ?? 0

  return (
    <div className="h-full overflow-y-auto">
      <div className="max-w-2xl mx-auto px-6 py-6">
        {/* Header (Spec 20 §3) */}
        <header className="mb-4">
          <h1 className="text-2xl font-semibold text-student-ink">Connect</h1>
          <p className="text-sm text-student-text mt-0.5">From the institutions you follow</p>
        </header>

        {/* Tabs + Manage following */}
        <div className="flex items-end justify-between border-b border-divider mb-5">
          <div className="flex gap-1">
            {TABS.map(t => (
              <button
                key={t.key}
                onClick={() => setTab(t.key)}
                className={`flex items-center gap-1.5 px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors ${
                  tab === t.key
                    ? 'border-cobalt text-cobalt'
                    : 'border-transparent text-student-text hover:text-student-ink'
                }`}
              >
                <t.icon size={14} />
                {t.label}
              </button>
            ))}
          </div>
          <button
            onClick={() => setManaging(true)}
            className="inline-flex sm:hidden items-center gap-1 px-3 py-1.5 mb-1 text-xs font-medium text-student-text hover:text-student-ink rounded-lg hover:bg-student-mist transition-colors"
          >
            Following ({followCount}) <ChevronDown size={13} />
          </button>
          <button
            onClick={() => setManaging(true)}
            className="hidden sm:inline-flex items-center gap-1 px-3 py-1.5 mb-1 text-xs font-medium text-student-text hover:text-student-ink rounded-lg hover:bg-student-mist transition-colors"
          >
            Manage following ({followCount}) <ChevronDown size={13} />
          </button>
        </div>

        {tab === 'updates' && <UpdatesTab />}
        {tab === 'events' && <EventsTab />}
        {tab === 'peers' && <PeersTab />}
      </div>

      {managing && <ManageFollowingPanel onClose={() => setManaging(false)} />}
    </div>
  )
}
