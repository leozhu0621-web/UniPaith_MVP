import { useNavigate } from 'react-router-dom'
import { Megaphone } from 'lucide-react'
import Card from '../../components/ui/Card'
import Button from '../../components/ui/Button'

export default function CampaignsPage() {
  const navigate = useNavigate()

  return (
    <div className="p-6 flex items-center justify-center min-h-[60vh]">
      <Card className="p-12 text-center max-w-md">
        <Megaphone size={56} className="mx-auto text-indigo-400 mb-4" />
        <h2 className="text-xl font-bold text-gray-900 mb-2">Coming in Phase 2</h2>
        <p className="text-gray-600 mb-6">
          Campaigns will allow you to create targeted outreach campaigns to prospective students using segments, templates, and scheduling.
        </p>
        <Button onClick={() => navigate('/i/messages')} className="flex items-center gap-2 mx-auto">
          Go to Messages
        </Button>
      </Card>
    </div>
  )
}
