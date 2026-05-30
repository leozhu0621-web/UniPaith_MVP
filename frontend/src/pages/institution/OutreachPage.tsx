import { useSearchParams } from 'react-router-dom'
import Tabs from '../../components/ui/Tabs'
import CampaignsPage from './CampaignsPage'
import PromotionsPage from './PromotionsPage'
import EventsPage from './EventsPage'
import PostsPage from './PostsPage'

// Unified Outreach workspace — Spec/04 §5.1 (?tab=campaigns|promotions|events|posts).
type OutreachTab = 'campaigns' | 'promotions' | 'events' | 'posts'

const tabs = [
  { id: 'campaigns', label: 'Campaigns' },
  { id: 'promotions', label: 'Promotions' },
  { id: 'events', label: 'Events' },
  { id: 'posts', label: 'Posts' },
]

export default function OutreachPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const param = searchParams.get('tab')
  const activeTab: OutreachTab = tabs.some(t => t.id === param) ? (param as OutreachTab) : 'campaigns'

  const handleTabChange = (tab: string) => {
    setSearchParams(prev => {
      const next = new URLSearchParams(prev)
      next.set('tab', tab)
      return next
    }, { replace: true })
  }

  return (
    <div className="p-6 space-y-4">
      <Tabs tabs={tabs} activeTab={activeTab} onChange={handleTabChange} />
      {activeTab === 'campaigns' && <CampaignsPage />}
      {activeTab === 'promotions' && <PromotionsPage />}
      {activeTab === 'events' && <EventsPage />}
      {activeTab === 'posts' && <PostsPage />}
    </div>
  )
}
