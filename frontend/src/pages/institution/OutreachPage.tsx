import { useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import Tabs from '../../components/ui/Tabs'
import CampaignsPage from './CampaignsPage'
import PromotionsPage from './PromotionsPage'
import EventsPage from './EventsPage'
import PostsPage from './PostsPage'

type OutreachTab = 'campaigns' | 'promotions' | 'events' | 'posts'

const tabs = [
  { id: 'campaigns', label: 'Campaigns' },
  { id: 'promotions', label: 'Promotions' },
  { id: 'events', label: 'Events' },
  { id: 'posts', label: 'Posts' },
]

export default function OutreachPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const initialTab = (searchParams.get('tab') as OutreachTab) || 'campaigns'
  const [activeTab, setActiveTab] = useState<OutreachTab>(initialTab)

  const handleTabChange = (tab: string) => {
    setActiveTab(tab as OutreachTab)
    setSearchParams({ tab })
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
