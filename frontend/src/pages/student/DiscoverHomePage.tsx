/**
 * Stage 1 (Discovery) — the Uni conversation (redesign).
 *
 * One warm, single-column conversation with Uni, a real college counselor.
 * No track tabs, layer pills, progress %, strategy CTA, or readiness/artifact
 * rails — just the conversation. A quiet "Your profile" link surfaces the
 * durable record (/s/profile). The unified session feeds goals/needs/identity
 * behind the scenes for matching.
 */
import { useNavigate } from 'react-router-dom'
import { Sparkles } from 'lucide-react'

import Card from '../../components/ui/Card'
import UniConversation from './discover/UniConversation'

export default function DiscoverHomePage() {
  const navigate = useNavigate()
  return (
    <div className="p-6 max-w-3xl mx-auto space-y-4">
      <header className="flex items-center justify-between gap-4">
        <p className="text-eyebrow text-secondary">Discover · with Uni</p>
        <button
          type="button"
          onClick={() => navigate('/s/profile')}
          className="inline-flex items-center gap-1.5 text-sm text-secondary hover:underline"
        >
          <Sparkles size={14} /> Your profile
        </button>
      </header>

      <Card className="p-4 sm:p-5">
        <UniConversation />
      </Card>
    </div>
  )
}
