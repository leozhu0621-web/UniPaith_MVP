import Card from '../../components/ui/Card'
import Badge from '../../components/ui/Badge'

export default function AdminAICenterStub() {
  return (
    <div className="p-6 max-w-3xl">
      <Card>
        <div className="p-8 space-y-4">
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-semibold">AI Center</h1>
            <Badge variant="warning">offline</Badge>
          </div>
          <p className="text-gray-600">
            UniEngine is being rebuilt. The pipeline, learning, and knowledge
            controls will return when the new architecture lands.
          </p>
          <p className="text-sm text-gray-500">
            Track the rebuild on the <code className="px-1.5 py-0.5 bg-gray-100 rounded">feat/ai-engine</code> branch.
          </p>
        </div>
      </Card>
    </div>
  )
}
