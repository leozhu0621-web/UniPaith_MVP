import { useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import FollowingFeed from './explore/FollowingFeed'
import DiscoverFeed from './explore/DiscoverFeed'
import SavedView from './explore/SavedView'
import SearchView from './explore/SearchView'
import { Rss, Globe, Search, Bookmark } from 'lucide-react'

type Tab = 'following' | 'discover' | 'search' | 'saved'

const TABS: { key: Tab; label: string; icon: typeof Rss }[] = [
  { key: 'following', label: 'Following', icon: Rss },
  { key: 'discover', label: 'Discover', icon: Globe },
  { key: 'search', label: 'Search', icon: Search },
  { key: 'saved', label: 'Saved', icon: Bookmark },
]

export default function ExplorePage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const rawTab = searchParams.get('tab')
  const initial: Tab = rawTab === 'discover' ? 'discover'
    : rawTab === 'search' ? 'search'
    : rawTab === 'saved' ? 'saved'
    : 'following'
  const [tab, setTab] = useState<Tab>(initial)

  const switchTab = (t: Tab) => {
    setTab(t)
    navigate(t === 'following' ? '/s/explore' : `/s/explore?tab=${t}`, { replace: true })
  }

  return (
    <div className="p-6">
      {/* Header */}
      <div className="max-w-2xl mx-auto mb-5">
        <h1 className="text-2xl font-semibold text-student-ink mb-1">Explore</h1>
        <p className="text-sm text-student-text mb-4">
          {tab === 'following' ? 'Updates from schools you follow.'
            : tab === 'discover' ? 'Browse programs, events, and school content.'
            : tab === 'search' ? 'Advanced search with filters.'
            : 'Programs you saved for later.'}
        </p>

        {/* Tab bar */}
        <div className="flex gap-0.5 border-b border-divider">
          {TABS.map(t => (
            <button
              key={t.key}
              onClick={() => switchTab(t.key)}
              className={`flex items-center gap-1.5 px-4 py-2.5 text-sm font-medium border-b-2 transition-colors ${
                tab === t.key
                  ? 'border-student text-student'
                  : 'border-transparent text-student-text hover:text-student-ink'
              }`}
            >
              <t.icon size={14} />
              {t.label}
            </button>
          ))}
        </div>
      </div>

      {/* Tab content */}
      {tab === 'following' && <FollowingFeed />}
      {tab === 'discover' && <DiscoverFeed />}
      {tab === 'search' && <SearchView />}
      {tab === 'saved' && <SavedView />}
    </div>
  )
}
