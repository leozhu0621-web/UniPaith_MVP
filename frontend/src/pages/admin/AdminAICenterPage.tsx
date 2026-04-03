import PipelineDashboard from '../../components/admin/pipeline/PipelineDashboard'
<<<<<<< HEAD
=======
import AdminMLPage from './AdminMLPage'
import AdminKnowledgePage from './AdminKnowledgePage'
import { useToastStore } from '../../stores/toast-store'

const UNLOCK_TTL_MS = 5 * 60 * 1000

const TABS = [
  { id: 'monitor', label: 'Monitor' },
  { id: 'controls', label: 'Controls' },
  { id: 'pipeline', label: 'Pipeline' },
  { id: 'learning', label: 'Learning' },
  { id: 'knowledge', label: 'Knowledge' },
  { id: 'maintenance', label: 'Maintenance' },
] as const

type TabId = (typeof TABS)[number]['id']

interface OpsError { message?: string }
>>>>>>> 7f0f036bb6318a30857aad13dd537c8ffa0ff11a

export default function AdminAICenterPage() {
  return (
    <div className="p-8 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">AI Engine</h1>
        <p className="text-sm text-gray-500">
          Continuous pipeline — Crawl, Extract, Train.
        </p>
      </div>
      <PipelineDashboard />
    </div>
  )
}
