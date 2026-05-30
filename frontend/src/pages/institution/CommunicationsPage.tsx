import { useSearchParams } from 'react-router-dom'
import Tabs from '../../components/ui/Tabs'
import TemplatesPage from './TemplatesPage'
import SegmentsPage from './SegmentsPage'
import MessagingPage from './MessagingPage'

// Unified Communications workspace — Spec/04 §5.1 (?tab=templates|segments|inbox).
type CommsTab = 'templates' | 'segments' | 'inbox'

const tabs = [
  { id: 'templates', label: 'Templates & AI Drafts' },
  { id: 'segments', label: 'Segments' },
  { id: 'inbox', label: 'Inbox' },
]

export default function CommunicationsPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const param = searchParams.get('tab')
  const activeTab: CommsTab = tabs.some(t => t.id === param) ? (param as CommsTab) : 'templates'

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
      {activeTab === 'templates' && <TemplatesPage />}
      {activeTab === 'segments' && <SegmentsPage />}
      {activeTab === 'inbox' && <MessagingPage />}
    </div>
  )
}
