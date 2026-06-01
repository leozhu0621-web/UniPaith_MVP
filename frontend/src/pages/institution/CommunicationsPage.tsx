import { useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import Tabs from '../../components/ui/Tabs'
import TemplatesPage from './TemplatesPage'
import SegmentsPage from './SegmentsPage'
import InstitutionInboxPage from './inbox/InstitutionInboxPage'

type CommsTab = 'templates' | 'segments' | 'inbox'

const tabs = [
  { id: 'inbox', label: 'Inbox' },
  { id: 'templates', label: 'Templates & AI Drafts' },
  { id: 'segments', label: 'Segments' },
]

// Spec 29 — institution Communications. The Inbox tab is the institution-side
// messaging surface (mirror of the student inbox, spec 17), with reason codes,
// assignment, AI drafts, applicant context, and bulk/segment messaging.
export default function CommunicationsPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const initialTab = (searchParams.get('tab') as CommsTab) || 'inbox'
  const [activeTab, setActiveTab] = useState<CommsTab>(initialTab)

  const handleTabChange = (tab: string) => {
    setActiveTab(tab as CommsTab)
    // Preserve a deep-linked thread only while on the inbox tab.
    setSearchParams(tab === 'inbox' ? { tab } : { tab })
  }

  return (
    <div className="flex h-[calc(100vh-4rem)] flex-col">
      <div className="shrink-0 px-6 pt-4">
        <Tabs tabs={tabs} activeTab={activeTab} onChange={handleTabChange} />
      </div>
      {activeTab === 'inbox' ? (
        <div className="min-h-0 flex-1">
          <InstitutionInboxPage />
        </div>
      ) : (
        <div className="flex-1 overflow-y-auto p-6">
          {activeTab === 'templates' && <TemplatesPage />}
          {activeTab === 'segments' && <SegmentsPage />}
        </div>
      )}
    </div>
  )
}
