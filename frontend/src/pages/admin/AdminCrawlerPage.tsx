import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  getCrawlerDashboard, getCrawlerSources, getCrawlerJobs,
  getReviewQueue, getReviewStats,
  triggerCrawl, triggerCrawlAll, seedDefaultSources,
  createCrawlerSource, deleteCrawlerSource,
  approveReviewItem, rejectReviewItem, applyAllEnrichments, crawlUrl,
} from '../../api/admin'
import { formatRelative } from '../../utils/format'
import Card from '../../components/ui/Card'
import Badge from '../../components/ui/Badge'
import Button from '../../components/ui/Button'
import Skeleton from '../../components/ui/Skeleton'
import Tabs from '../../components/ui/Tabs'
import Modal from '../../components/ui/Modal'
import Input from '../../components/ui/Input'
import { useToastStore } from '../../stores/toast-store'
import { errorMessage } from '../../utils/errors'
import {
  Globe, Play, Plus, Trash2, CheckCircle, XCircle,
  Zap, ExternalLink,
} from 'lucide-react'

interface CrawlerSourceRow {
  id: string
  name: string
  base_url?: string
  source_type?: string
  is_active?: boolean
  schedule_cron?: string | null
}

interface CrawlerJobRow {
  id: string
  status?: string
  source_name?: string
  source_id?: string
  created_at?: string
  pages_crawled?: number
  programs_extracted?: number
  started_at?: string
}

interface ReviewQueueRow {
  id: string
  title?: string
  status?: string
  created_at?: string
  program_name?: string
  institution_name?: string
  source_url?: string
  extracted_data?: Record<string, unknown>
}

export default function AdminCrawlerPage() {
  const qc = useQueryClient()
  const addToast = useToastStore(s => s.addToast)
  const [activeTab, setActiveTab] = useState('overview')
  const [showAddSource, setShowAddSource] = useState(false)
  const [showCrawlUrl, setShowCrawlUrl] = useState(false)
  const [newSource, setNewSource] = useState({ name: '', base_url: '', source_type: 'university', schedule_cron: '' })
  const [crawlUrlInput, setCrawlUrlInput] = useState('')
  const [rejectReason, setRejectReason] = useState('')
  const [rejectId, setRejectId] = useState<string | null>(null)

  const dashboardQ = useQuery({ queryKey: ['admin', 'crawler', 'dashboard'], queryFn: getCrawlerDashboard })
  const sourcesQ = useQuery({ queryKey: ['admin', 'crawler', 'sources'], queryFn: () => getCrawlerSources({ limit: 50 }) })
  const jobsQ = useQuery({ queryKey: ['admin', 'crawler', 'jobs'], queryFn: () => getCrawlerJobs({ limit: 30 }) })
  const reviewQ = useQuery({ queryKey: ['admin', 'crawler', 'review'], queryFn: () => getReviewQueue({ limit: 30 }) })
  const reviewStatsQ = useQuery({ queryKey: ['admin', 'crawler', 'review-stats'], queryFn: getReviewStats })

  const crawlMut = useMutation({
    mutationFn: triggerCrawl,
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['admin', 'crawler'] }); addToast('Crawl triggered', 'success') },
    onError: (e: unknown) => addToast(errorMessage(e), 'error'),
  })
  const crawlAllMut = useMutation({
    mutationFn: triggerCrawlAll,
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['admin', 'crawler'] }); addToast('Crawl-all triggered', 'success') },
    onError: (e: unknown) => addToast(errorMessage(e), 'error'),
  })
  const seedMut = useMutation({
    mutationFn: seedDefaultSources,
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['admin', 'crawler'] }); addToast('Default sources seeded', 'success') },
    onError: (e: unknown) => addToast(errorMessage(e), 'error'),
  })
  const addSourceMut = useMutation({
    mutationFn: createCrawlerSource,
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['admin', 'crawler'] }); setShowAddSource(false); addToast('Source added', 'success') },
    onError: (e: unknown) => addToast(errorMessage(e), 'error'),
  })
  const delSourceMut = useMutation({
    mutationFn: deleteCrawlerSource,
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['admin', 'crawler'] }); addToast('Source deleted', 'success') },
    onError: (e: unknown) => addToast(errorMessage(e), 'error'),
  })
  const approveMut = useMutation({
    mutationFn: (id: string) => approveReviewItem(id),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['admin', 'crawler'] }); addToast('Approved', 'success') },
    onError: (e: unknown) => addToast(errorMessage(e), 'error'),
  })
  const rejectMut = useMutation({
    mutationFn: ({ id, reason }: { id: string; reason: string }) => rejectReviewItem(id, { reason }),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['admin', 'crawler'] }); setRejectId(null); addToast('Rejected', 'success') },
    onError: (e: unknown) => addToast(errorMessage(e), 'error'),
  })
  const enrichMut = useMutation({
    mutationFn: applyAllEnrichments,
    onSuccess: () => { addToast('Enrichments applied', 'success') },
    onError: (e: unknown) => addToast(errorMessage(e), 'error'),
  })
  const crawlUrlMut = useMutation({
    mutationFn: (url: string) => crawlUrl({ url }),
    onSuccess: () => { setShowCrawlUrl(false); addToast('URL crawled', 'success') },
    onError: (e: unknown) => addToast(errorMessage(e), 'error'),
  })

  const dashboard = dashboardQ.data
  const sources: CrawlerSourceRow[] = Array.isArray(sourcesQ.data)
    ? sourcesQ.data
    : sourcesQ.data?.sources ?? []
  const jobs: CrawlerJobRow[] = Array.isArray(jobsQ.data) ? jobsQ.data : jobsQ.data?.jobs ?? []
  const reviewItems: ReviewQueueRow[] = Array.isArray(reviewQ.data) ? reviewQ.data : reviewQ.data?.items ?? []
  const rStats = reviewStatsQ.data

  const tabs = [
    { id: 'overview', label: 'Overview' },
    { id: 'sources', label: `Sources (${sources.length})` },
    { id: 'jobs', label: `Jobs (${jobs.length})` },
    { id: 'review', label: `Review Queue (${reviewItems.length})` },
  ]

  if (dashboardQ.isLoading) {
    return <div className="p-8"><Skeleton className="h-96" /></div>
  }

  return (
    <div className="p-8 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Crawler Management</h1>
          <p className="text-sm text-gray-500">Data sources, crawl jobs, and program review queue</p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="secondary" size="sm" onClick={() => setShowCrawlUrl(true)}>
            <Globe size={14} className="mr-1" /> Crawl URL
          </Button>
          <Button variant="secondary" size="sm" onClick={() => crawlAllMut.mutate()} disabled={crawlAllMut.isPending}>
            <Play size={14} className="mr-1" /> Crawl All Due
          </Button>
          <Button variant="secondary" size="sm" onClick={() => enrichMut.mutate()} disabled={enrichMut.isPending}>
            <Zap size={14} className="mr-1" /> Apply Enrichments
          </Button>
        </div>
      </div>

      <Tabs tabs={tabs} activeTab={activeTab} onChange={setActiveTab} />

      {/* Overview Tab */}
      {activeTab === 'overview' && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <Card className="p-5">
            <p className="text-xs text-gray-500 uppercase">Active Sources</p>
            <p className="text-3xl font-bold mt-1">{dashboard?.active_sources ?? sources.length}</p>
          </Card>
          <Card className="p-5">
            <p className="text-xs text-gray-500 uppercase">Total Jobs</p>
            <p className="text-3xl font-bold mt-1">{dashboard?.total_jobs ?? jobs.length}</p>
          </Card>
          <Card className="p-5">
            <p className="text-xs text-gray-500 uppercase">Pending Review</p>
            <p className="text-3xl font-bold mt-1">{rStats?.pending ?? reviewItems.length}</p>
          </Card>
          <Card className="p-5">
            <p className="text-xs text-gray-500 uppercase">Approved</p>
            <p className="text-3xl font-bold mt-1">{rStats?.approved ?? 0}</p>
          </Card>
        </div>
      )}

      {/* Sources Tab */}
      {activeTab === 'sources' && (
        <>
          <div className="flex gap-2">
            <Button size="sm" onClick={() => setShowAddSource(true)}>
              <Plus size={14} className="mr-1" /> Add Source
            </Button>
            <Button variant="secondary" size="sm" onClick={() => seedMut.mutate()} disabled={seedMut.isPending}>
              Seed Defaults
            </Button>
          </div>
          <Card className="overflow-hidden">
            <table className="w-full">
              <thead>
                <tr className="bg-gray-50 border-b">
                  <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase">Name</th>
                  <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase">URL</th>
                  <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase">Type</th>
                  <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase">Schedule</th>
                  <th className="text-right px-6 py-3 text-xs font-medium text-gray-500 uppercase">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {sources.map(s => (
                  <tr key={s.id} className="hover:bg-gray-50">
                    <td className="px-6 py-3 text-sm font-medium">{s.name}</td>
                    <td className="px-6 py-3 text-sm text-gray-500 truncate max-w-xs">{s.base_url}</td>
                    <td className="px-6 py-3"><Badge variant="info">{s.source_type ?? 'university'}</Badge></td>
                    <td className="px-6 py-3 text-sm text-gray-500">{s.schedule_cron || '—'}</td>
                    <td className="px-6 py-3 text-right space-x-2">
                      <Button size="sm" variant="secondary" onClick={() => crawlMut.mutate(s.id)} disabled={crawlMut.isPending}>
                        <Play size={12} />
                      </Button>
                      <Button size="sm" variant="secondary" onClick={() => delSourceMut.mutate(s.id)} disabled={delSourceMut.isPending}
                        className="text-red-600 border-red-200 hover:bg-red-50">
                        <Trash2 size={12} />
                      </Button>
                    </td>
                  </tr>
                ))}
                {sources.length === 0 && (
                  <tr><td colSpan={5} className="px-6 py-12 text-center text-gray-400 text-sm">No sources configured</td></tr>
                )}
              </tbody>
            </table>
          </Card>
        </>
      )}

      {/* Jobs Tab */}
      {activeTab === 'jobs' && (
        <Card className="overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="bg-gray-50 border-b">
                <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase">Job ID</th>
                <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase">Source</th>
                <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase">Status</th>
                <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase">Pages</th>
                <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase">Programs</th>
                <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase">Started</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {jobs.map(j => (
                <tr key={j.id} className="hover:bg-gray-50">
                  <td className="px-6 py-3"><code className="text-xs text-gray-500">{j.id?.slice(0, 8)}...</code></td>
                  <td className="px-6 py-3 text-sm">{j.source_name ?? j.source_id?.slice(0, 8)}</td>
                  <td className="px-6 py-3">
                    <Badge variant={
                      j.status === 'completed' ? 'success' :
                      j.status === 'running' ? 'warning' :
                      j.status === 'failed' ? 'danger' : 'neutral'
                    }>{j.status}</Badge>
                  </td>
                  <td className="px-6 py-3 text-sm">{j.pages_crawled ?? 0}</td>
                  <td className="px-6 py-3 text-sm">{j.programs_extracted ?? 0}</td>
                  <td className="px-6 py-3 text-sm text-gray-500">{formatRelative(j.started_at ?? j.created_at)}</td>
                </tr>
              ))}
              {jobs.length === 0 && (
                <tr><td colSpan={6} className="px-6 py-12 text-center text-gray-400 text-sm">No crawl jobs yet</td></tr>
              )}
            </tbody>
          </table>
        </Card>
      )}

      {/* Review Queue Tab */}
      {activeTab === 'review' && (
        <div className="space-y-4">
          {reviewItems.length === 0 ? (
            <Card className="p-12 text-center text-gray-400">No items pending review</Card>
          ) : (
            reviewItems.map(item => (
              <Card key={item.id} className="p-5">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h3 className="font-medium text-gray-900">
                      {String(item.program_name ?? item.extracted_data?.program_name ?? 'Unnamed Program')}
                    </h3>
                    <p className="text-sm text-gray-500 mt-1">
                      {String(item.institution_name ?? item.extracted_data?.institution_name ?? '')}
                    </p>
                    <div className="flex gap-4 mt-2 text-xs text-gray-400">
                      {item.extracted_data?.degree_type != null && (
                        <span>Degree: {String(item.extracted_data.degree_type)}</span>
                      )}
                      {item.extracted_data?.tuition != null && (
                        <span>Tuition: ${String(item.extracted_data.tuition)}</span>
                      )}
                      {item.source_url && (
                        <a href={item.source_url} target="_blank" rel="noreferrer" className="text-indigo-500 hover:underline flex items-center gap-1">
                          Source <ExternalLink size={10} />
                        </a>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center gap-2 ml-4">
                    <Button size="sm" onClick={() => approveMut.mutate(item.id)} disabled={approveMut.isPending}>
                      <CheckCircle size={14} className="mr-1" /> Approve
                    </Button>
                    <Button size="sm" variant="secondary" onClick={() => setRejectId(item.id)}
                      className="text-red-600 border-red-200 hover:bg-red-50">
                      <XCircle size={14} className="mr-1" /> Reject
                    </Button>
                  </div>
                </div>
              </Card>
            ))
          )}
        </div>
      )}

      {/* Add Source Modal */}
      <Modal isOpen={showAddSource} onClose={() => setShowAddSource(false)} title="Add Data Source">
        <div className="space-y-4">
          <Input label="Name" value={newSource.name} onChange={e => setNewSource(p => ({ ...p, name: e.target.value }))} placeholder="e.g. MIT" />
          <Input label="Base URL" value={newSource.base_url} onChange={e => setNewSource(p => ({ ...p, base_url: e.target.value }))} placeholder="https://..." />
          <Input label="Source Type" value={newSource.source_type} onChange={e => setNewSource(p => ({ ...p, source_type: e.target.value }))} />
          <Input label="Schedule (cron)" value={newSource.schedule_cron} onChange={e => setNewSource(p => ({ ...p, schedule_cron: e.target.value }))} placeholder="0 2 * * 1" />
          <div className="flex justify-end gap-2">
            <Button variant="secondary" onClick={() => setShowAddSource(false)}>Cancel</Button>
            <Button onClick={() => addSourceMut.mutate(newSource)} disabled={addSourceMut.isPending || !newSource.name || !newSource.base_url}>
              Add Source
            </Button>
          </div>
        </div>
      </Modal>

      {/* Crawl URL Modal */}
      <Modal isOpen={showCrawlUrl} onClose={() => setShowCrawlUrl(false)} title="Crawl a URL">
        <div className="space-y-4">
          <Input label="URL" value={crawlUrlInput} onChange={e => setCrawlUrlInput(e.target.value)} placeholder="https://..." />
          <div className="flex justify-end gap-2">
            <Button variant="secondary" onClick={() => setShowCrawlUrl(false)}>Cancel</Button>
            <Button onClick={() => crawlUrlMut.mutate(crawlUrlInput)} disabled={crawlUrlMut.isPending || !crawlUrlInput}>
              Crawl
            </Button>
          </div>
        </div>
      </Modal>

      {/* Reject Modal */}
      <Modal isOpen={!!rejectId} onClose={() => setRejectId(null)} title="Reject Program">
        <div className="space-y-4">
          <Input label="Reason" value={rejectReason} onChange={e => setRejectReason(e.target.value)} placeholder="Why is this being rejected?" />
          <div className="flex justify-end gap-2">
            <Button variant="secondary" onClick={() => setRejectId(null)}>Cancel</Button>
            <Button onClick={() => { if (rejectId) rejectMut.mutate({ id: rejectId, reason: rejectReason }) }}
              disabled={rejectMut.isPending || !rejectReason}
              className="bg-red-600 hover:bg-red-700">
              Reject
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  )
}
