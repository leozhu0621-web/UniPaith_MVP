import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts'
import apiClient from '../../api/client'
import Card from '../../components/ui/Card'
import Button from '../../components/ui/Button'
import Modal from '../../components/ui/Modal'

interface DashboardData {
  status: string
  rpm: number
  last_activity_at: string | null
  queue: { pending: number; completed: number; failed: number; total: number }
  recent_activity: {
    url: string; domain: string; status: string
    updated_at: string | null; error: string | null
  }[]
  throughput_24h: { hour: string; docs_crawled: number; docs_failed: number }[]
  domains: {
    domain: string; doc_count: number; pending: number
    failed: number; avg_quality: number
  }[]
  errors: {
    id: string; url: string; domain: string
    last_error: string; consecutive_failures: number
    last_crawled_at: string | null
  }[]
  discovery: Record<string, number>
  seed_urls_count: number
  total_domains: number
}

function timeAgo(iso: string | null): string {
  if (!iso) return '—'
  const diff = Date.now() - new Date(iso).getTime()
  if (diff < 5_000) return 'just now'
  if (diff < 60_000) return `${Math.round(diff / 1000)}s ago`
  if (diff < 3_600_000) return `${Math.round(diff / 60_000)}m ago`
  return `${Math.round(diff / 3_600_000)}h ago`
}

function truncateUrl(url: string, max = 50): string {
  if (url.length <= max) return url
  return url.slice(0, max - 3) + '...'
}

const STATUS_DOT: Record<string, string> = {
  completed: 'bg-green-500',
  pending: 'bg-gray-400',
  failed: 'bg-red-500',
  running: 'bg-green-500',
}

function StatCard({ label, value, color }: { label: string; value: number | string; color?: string }) {
  return (
    <div className="text-center px-4">
      <p className={`text-2xl font-bold ${color || 'text-gray-900'}`}>{typeof value === 'number' ? value.toLocaleString() : value}</p>
      <p className="text-xs text-gray-500 mt-0.5">{label}</p>
    </div>
  )
}

export default function AdminCrawlerDashboardPage() {
  const queryClient = useQueryClient()
  const [addUrlsOpen, setAddUrlsOpen] = useState(false)
  const [urlsText, setUrlsText] = useState('')

  const { data, isLoading } = useQuery<DashboardData>({
    queryKey: ['crawler-dashboard-v2'],
    queryFn: () => apiClient.get('/admin/crawler/dashboard-v2').then(r => r.data),
    refetchInterval: 5_000,
  })

  const retryMut = useMutation({
    mutationFn: (ids: string[]) =>
      apiClient.post('/admin/crawler/retry', { frontier_ids: ids }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['crawler-dashboard-v2'] }),
  })

  const addUrlsMut = useMutation({
    mutationFn: (urls: string[]) =>
      apiClient.post('/admin/crawler/add-urls', { urls }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['crawler-dashboard-v2'] })
      setAddUrlsOpen(false)
      setUrlsText('')
    },
  })

  const deleteMut = useMutation({
    mutationFn: (id: string) =>
      apiClient.delete(`/admin/crawler/frontier/${id}`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['crawler-dashboard-v2'] }),
  })

  const forceMut = useMutation({
    mutationFn: () =>
      apiClient.post('/admin/pipeline/force', { action: 'discover' }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['crawler-dashboard-v2'] }),
  })

  const toggleMut = useMutation({
    mutationFn: (enabled: boolean) =>
      apiClient.post('/admin/pipeline/toggle', { enabled }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['crawler-dashboard-v2'] }),
  })

  if (isLoading || !data) {
    return (
      <div className="p-8 space-y-4">
        <div className="animate-pulse space-y-4">
          <div className="h-10 bg-gray-200 rounded w-48" />
          <div className="h-48 bg-gray-100 rounded" />
          <div className="h-64 bg-gray-100 rounded" />
        </div>
      </div>
    )
  }

  const isOn = data.status !== 'paused' && data.status !== 'off'
  const discoveryEntries = Object.entries(data.discovery).sort((a, b) => b[1] - a[1])
  const discoveryChart = discoveryEntries.map(([method, count]) => ({
    method: method.replace(/_/g, ' '),
    count,
  }))

  const throughputData = data.throughput_24h.map(t => ({
    ...t,
    label: t.hour ? new Date(t.hour).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : '',
  }))

  return (
    <div className="p-8 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Crawler</h1>
          <p className="text-sm text-gray-500">Data collection pipeline — discover, fetch, and queue for extraction.</p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => toggleMut.mutate(!isOn)}
            disabled={toggleMut.isPending}
            className={`relative inline-flex h-7 w-12 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-offset-1 ${
              isOn ? 'bg-green-500 focus:ring-green-400' : 'bg-gray-300 focus:ring-gray-400'
            }`}
          >
            <span className={`inline-block h-5 w-5 transform rounded-full bg-white shadow transition-transform ${
              isOn ? 'translate-x-6' : 'translate-x-1'
            }`} />
          </button>
          <span className={`text-sm font-semibold ${isOn ? 'text-green-700' : 'text-gray-500'}`}>
            {isOn ? 'Running' : 'Off'}
          </span>
        </div>
      </div>

      {/* Stats bar */}
      <Card className="p-4">
        <div className="flex items-center justify-around divide-x divide-gray-200">
          <StatCard label="Pending" value={data.queue.pending} color="text-yellow-600" />
          <StatCard label="Completed" value={data.queue.completed} color="text-green-600" />
          <StatCard label="Failed" value={data.queue.failed} color="text-red-600" />
          <StatCard label="Domains" value={data.total_domains} />
          <StatCard label="RPM" value={data.rpm} />
          <StatCard label="Last Activity" value={timeAgo(data.last_activity_at)} />
        </div>
      </Card>

      {/* Row 1: Live activity + Throughput chart */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Live activity feed */}
        <Card className="p-4">
          <h2 className="text-sm font-semibold text-gray-700 mb-3">Live Activity</h2>
          <div className="max-h-64 overflow-y-auto space-y-1">
            {data.recent_activity.length === 0 ? (
              <p className="text-xs text-gray-400 py-4 text-center">No recent activity</p>
            ) : (
              data.recent_activity.map((item, i) => (
                <div key={i} className="flex items-center gap-2 py-1 px-2 rounded hover:bg-gray-50 text-xs">
                  <span className={`h-2 w-2 rounded-full flex-shrink-0 ${STATUS_DOT[item.status] || 'bg-gray-300'}`} />
                  <span className="text-gray-500 w-24 flex-shrink-0 truncate">{item.domain}</span>
                  <span className="text-gray-700 flex-1 truncate" title={item.url}>{truncateUrl(item.url, 60)}</span>
                  <span className="text-gray-400 flex-shrink-0">{timeAgo(item.updated_at)}</span>
                </div>
              ))
            )}
          </div>
        </Card>

        {/* Throughput chart */}
        <Card className="p-4">
          <h2 className="text-sm font-semibold text-gray-700 mb-3">Throughput (24h)</h2>
          {throughputData.length === 0 ? (
            <p className="text-xs text-gray-400 py-12 text-center">No data yet</p>
          ) : (
            <ResponsiveContainer width="100%" height={220}>
              <AreaChart data={throughputData}>
                <XAxis dataKey="label" tick={{ fontSize: 10 }} interval="preserveStartEnd" />
                <YAxis tick={{ fontSize: 10 }} width={30} />
                <Tooltip contentStyle={{ fontSize: 12 }} />
                <Area
                  type="monotone" dataKey="docs_crawled" name="Crawled"
                  stackId="1" stroke="#22c55e" fill="#bbf7d0"
                />
                <Area
                  type="monotone" dataKey="docs_failed" name="Failed"
                  stackId="1" stroke="#ef4444" fill="#fecaca"
                />
              </AreaChart>
            </ResponsiveContainer>
          )}
        </Card>
      </div>

      {/* Row 2: Queue breakdown + Domain breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Queue breakdown */}
        <Card className="p-4">
          <h2 className="text-sm font-semibold text-gray-700 mb-3">Queue Breakdown</h2>
          <div className="flex h-6 rounded-full overflow-hidden bg-gray-100">
            {data.queue.completed > 0 && (
              <div
                className="bg-green-500 transition-all"
                style={{ width: `${(data.queue.completed / Math.max(data.queue.total, 1)) * 100}%` }}
                title={`Completed: ${data.queue.completed}`}
              />
            )}
            {data.queue.pending > 0 && (
              <div
                className="bg-yellow-400 transition-all"
                style={{ width: `${(data.queue.pending / Math.max(data.queue.total, 1)) * 100}%` }}
                title={`Pending: ${data.queue.pending}`}
              />
            )}
            {data.queue.failed > 0 && (
              <div
                className="bg-red-500 transition-all"
                style={{ width: `${(data.queue.failed / Math.max(data.queue.total, 1)) * 100}%` }}
                title={`Failed: ${data.queue.failed}`}
              />
            )}
          </div>
          <div className="flex justify-between mt-2 text-xs text-gray-500">
            <span className="flex items-center gap-1"><span className="h-2 w-2 rounded-full bg-green-500" /> {data.queue.completed} completed</span>
            <span className="flex items-center gap-1"><span className="h-2 w-2 rounded-full bg-yellow-400" /> {data.queue.pending} pending</span>
            <span className="flex items-center gap-1"><span className="h-2 w-2 rounded-full bg-red-500" /> {data.queue.failed} failed</span>
          </div>
          <p className="text-xs text-gray-400 mt-2 text-center">{data.queue.total.toLocaleString()} total frontier entries</p>
        </Card>

        {/* Domain breakdown */}
        <Card className="p-4">
          <h2 className="text-sm font-semibold text-gray-700 mb-3">Top Domains</h2>
          <div className="max-h-52 overflow-y-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="text-gray-400 border-b border-gray-100">
                  <th className="text-left py-1 font-medium">Domain</th>
                  <th className="text-right py-1 font-medium">Docs</th>
                  <th className="text-right py-1 font-medium">Pending</th>
                  <th className="text-right py-1 font-medium">Failed</th>
                  <th className="text-right py-1 font-medium">Quality</th>
                </tr>
              </thead>
              <tbody>
                {data.domains.map(d => (
                  <tr key={d.domain} className="border-b border-gray-50 hover:bg-gray-50">
                    <td className="py-1.5 text-gray-700 truncate max-w-[160px]" title={d.domain}>{d.domain}</td>
                    <td className="py-1.5 text-right font-mono text-gray-800">{d.doc_count}</td>
                    <td className="py-1.5 text-right font-mono text-yellow-600">{d.pending}</td>
                    <td className="py-1.5 text-right font-mono text-red-600">{d.failed}</td>
                    <td className="py-1.5 text-right">
                      <div className="flex items-center justify-end gap-1">
                        <div className="w-12 bg-gray-100 rounded-full h-1.5">
                          <div
                            className={`h-1.5 rounded-full ${d.avg_quality >= 0.7 ? 'bg-green-500' : d.avg_quality >= 0.4 ? 'bg-yellow-500' : 'bg-red-500'}`}
                            style={{ width: `${Math.min(100, d.avg_quality * 100)}%` }}
                          />
                        </div>
                        <span className="font-mono text-gray-600 w-8">{(d.avg_quality * 100).toFixed(0)}%</span>
                      </div>
                    </td>
                  </tr>
                ))}
                {data.domains.length === 0 && (
                  <tr><td colSpan={5} className="text-center py-4 text-gray-400">No domain data</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </Card>
      </div>

      {/* Row 3: Errors panel (full width) */}
      <Card className="p-4">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-sm font-semibold text-gray-700">
            Errors ({data.errors.length})
          </h2>
          {data.errors.length > 0 && (
            <Button
              size="sm" variant="secondary"
              onClick={() => retryMut.mutate(data.errors.map(e => e.id))}
              disabled={retryMut.isPending}
            >
              Retry All
            </Button>
          )}
        </div>
        {data.errors.length === 0 ? (
          <p className="text-xs text-gray-400 py-4 text-center">No errors</p>
        ) : (
          <div className="max-h-56 overflow-y-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="text-gray-400 border-b border-gray-100">
                  <th className="text-left py-1 font-medium">URL</th>
                  <th className="text-left py-1 font-medium">Error</th>
                  <th className="text-right py-1 font-medium">Fails</th>
                  <th className="text-right py-1 font-medium">Last Attempt</th>
                  <th className="text-right py-1 font-medium w-24">Actions</th>
                </tr>
              </thead>
              <tbody>
                {data.errors.map(e => (
                  <tr key={e.id} className="border-b border-gray-50 hover:bg-gray-50">
                    <td className="py-1.5 text-gray-700 truncate max-w-[200px]" title={e.url}>
                      {truncateUrl(e.url, 45)}
                    </td>
                    <td className="py-1.5 text-red-600 truncate max-w-[200px]" title={e.last_error}>
                      {e.last_error ? truncateUrl(e.last_error, 50) : '—'}
                    </td>
                    <td className="py-1.5 text-right font-mono text-gray-800">{e.consecutive_failures}</td>
                    <td className="py-1.5 text-right text-gray-500">{timeAgo(e.last_crawled_at)}</td>
                    <td className="py-1.5 text-right">
                      <div className="flex gap-1 justify-end">
                        <button
                          className="text-blue-600 hover:text-blue-800 font-medium"
                          onClick={() => retryMut.mutate([e.id])}
                          disabled={retryMut.isPending}
                        >
                          Retry
                        </button>
                        <button
                          className="text-gray-400 hover:text-red-600 font-medium"
                          onClick={() => deleteMut.mutate(e.id)}
                          disabled={deleteMut.isPending}
                        >
                          Del
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {/* Row 4: Discovery stats + Source management */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Discovery stats */}
        <Card className="p-4">
          <h2 className="text-sm font-semibold text-gray-700 mb-3">Discovery Methods</h2>
          {discoveryChart.length === 0 ? (
            <p className="text-xs text-gray-400 py-8 text-center">No discovery data</p>
          ) : (
            <ResponsiveContainer width="100%" height={180}>
              <BarChart data={discoveryChart} layout="vertical" margin={{ left: 90 }}>
                <XAxis type="number" tick={{ fontSize: 10 }} />
                <YAxis type="category" dataKey="method" tick={{ fontSize: 10 }} width={85} />
                <Tooltip contentStyle={{ fontSize: 12 }} />
                <Bar dataKey="count" fill="#6366f1" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </Card>

        {/* Source management */}
        <Card className="p-4">
          <h2 className="text-sm font-semibold text-gray-700 mb-3">Source Management</h2>
          <div className="space-y-3">
            <div className="flex gap-3 text-xs">
              <div className="flex-1 border border-gray-200 rounded-lg p-3 text-center">
                <p className="text-lg font-bold text-gray-900">{data.seed_urls_count}</p>
                <p className="text-gray-500">Seed / manual URLs</p>
              </div>
              <div className="flex-1 border border-gray-200 rounded-lg p-3 text-center">
                <p className="text-lg font-bold text-gray-900">{data.queue.total - data.seed_urls_count}</p>
                <p className="text-gray-500">Auto-discovered</p>
              </div>
              <div className="flex-1 border border-gray-200 rounded-lg p-3 text-center">
                <p className="text-lg font-bold text-gray-900">{data.total_domains}</p>
                <p className="text-gray-500">Total domains</p>
              </div>
            </div>
            <div className="flex gap-2">
              <Button size="sm" onClick={() => setAddUrlsOpen(true)}>
                Add URLs
              </Button>
              <Button
                size="sm" variant="secondary"
                onClick={() => forceMut.mutate()}
                disabled={forceMut.isPending}
              >
                Force Discovery
              </Button>
            </div>
          </div>
        </Card>
      </div>

      {/* Add URLs modal */}
      <Modal isOpen={addUrlsOpen} onClose={() => setAddUrlsOpen(false)} title="Add URLs to Frontier">
          <div className="space-y-3">
            <textarea
              className="w-full border border-gray-300 rounded-lg p-3 text-sm font-mono h-40 focus:outline-none focus:ring-2 focus:ring-blue-400"
              placeholder="Paste URLs, one per line..."
              value={urlsText}
              onChange={e => setUrlsText(e.target.value)}
            />
            <div className="flex justify-end gap-2">
              <Button variant="secondary" onClick={() => setAddUrlsOpen(false)}>Cancel</Button>
              <Button
                onClick={() => {
                  const urls = urlsText.split('\n').map(s => s.trim()).filter(Boolean)
                  if (urls.length) addUrlsMut.mutate(urls)
                }}
                disabled={addUrlsMut.isPending || !urlsText.trim()}
              >
                {addUrlsMut.isPending ? 'Adding...' : `Add ${urlsText.split('\n').filter(s => s.trim()).length} URLs`}
              </Button>
            </div>
          </div>
        </Modal>
    </div>
  )
}
