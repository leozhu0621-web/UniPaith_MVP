import { useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import Tabs from '../../components/ui/Tabs'
import TemplatesPage from './TemplatesPage'
import SegmentsPage from './SegmentsPage'
import MessagingPage from './MessagingPage'

type CommsTab = 'templates' | 'segments' | 'inbox'

const tabs = [
  { id: 'templates', label: 'Templates & AI Drafts' },
  { id: 'segments', label: 'Segments' },
  { id: 'inbox', label: 'Inbox' },
]

export default function CommunicationsPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const initialTab = (searchParams.get('tab') as CommsTab) || 'templates'
  const [activeTab, setActiveTab] = useState<CommsTab>(initialTab)

  const handleTabChange = (tab: string) => {
    setActiveTab(tab as CommsTab)
    setSearchParams({ tab })
  }

  return (
    <div className="p-6 space-y-4">
      <Tabs tabs={tabs} activeTab={activeTab} onChange={handleTabChange} />
      {activeTab === 'templates' && <TemplatesPage />}
      {activeTab === 'segments' && <SegmentsPage />}
      {activeTab === 'inbox' && <MessagingPage />}
    </div>
  )
}
