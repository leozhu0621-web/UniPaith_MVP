import PipelineDashboard from '../../components/admin/pipeline/PipelineDashboard'

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
