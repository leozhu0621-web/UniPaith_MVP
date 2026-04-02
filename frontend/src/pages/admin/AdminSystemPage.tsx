import { useQuery } from '@tanstack/react-query'
import { getAdminActionAudit } from '../../api/admin'
import Card from '../../components/ui/Card'
import Button from '../../components/ui/Button'
import { RefreshCw } from 'lucide-react'

export default function AdminSystemPage() {
  const adminAuditQ = useQuery({
    queryKey: ['admin', 'audit', 'actions', 'system'],
    queryFn: () => getAdminActionAudit({ limit: 100 }),
    refetchInterval: 10000,
  })

  return (
    <div className="p-8 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">System Settings</h1>
        <p className="text-sm text-gray-500">Environment info and admin action history</p>
      </div>

      <Card className="p-6">
        <h3 className="text-sm font-semibold text-gray-700 mb-4">Environment</h3>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-gray-50 rounded-lg p-3">
            <p className="text-xs text-gray-500">API URL</p>
            <p className="text-sm font-mono text-gray-800 mt-1">{import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'}</p>
          </div>
          <div className="bg-gray-50 rounded-lg p-3">
            <p className="text-xs text-gray-500">Frontend Build</p>
            <p className="text-sm font-mono text-gray-800 mt-1">{import.meta.env.MODE}</p>
          </div>
          <div className="bg-gray-50 rounded-lg p-3">
            <p className="text-xs text-gray-500">Node Env</p>
            <p className="text-sm font-mono text-gray-800 mt-1">{import.meta.env.PROD ? 'production' : 'development'}</p>
          </div>
          <div className="bg-gray-50 rounded-lg p-3">
            <p className="text-xs text-gray-500">Version</p>
            <p className="text-sm font-mono text-gray-800 mt-1">MVP 0.1.0</p>
          </div>
        </div>
      </Card>

      <Card className="p-4 bg-blue-50 border-blue-200">
        <p className="text-sm text-blue-800">
          AI policy, controls, bootstrap, and maintenance actions have moved to{' '}
          <a href="/admin/ai" className="font-semibold underline">AI Center</a>.
        </p>
      </Card>

      <Card className="p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="font-semibold text-gray-900">Admin Action History</h3>
            <p className="text-xs text-gray-500">Full feed of user, institution, and AI admin actions</p>
          </div>
          <Button variant="secondary" onClick={() => adminAuditQ.refetch()} disabled={adminAuditQ.isFetching}>
            <RefreshCw size={14} className={`mr-2 ${adminAuditQ.isFetching ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>
        <div className="space-y-2 max-h-96 overflow-auto">
          {(adminAuditQ.data?.items ?? []).length === 0 ? (
            <p className="text-sm text-gray-500">No admin actions recorded yet.</p>
          ) : (
            (adminAuditQ.data?.items ?? []).map((event: any) => (
              <div key={event.id} className="border border-gray-200 rounded-lg p-3">
                <div className="flex items-center justify-between">
                  <p className="text-sm font-medium text-gray-900">{event.action}</p>
                  <p className="text-xs text-gray-500">{event.created_at}</p>
                </div>
                <p className="text-xs text-gray-600 mt-1">
                  {event.entity_type} · {event.entity_id}
                </p>
                {event.payload_json?.reason && (
                  <p className="text-xs text-gray-500 mt-1">Reason: {event.payload_json.reason}</p>
                )}
              </div>
            ))
          )}
        </div>
      </Card>
    </div>
  )
}
