import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  Brain,
  Clock,
  ExternalLink,
  FileText,
  Globe,
  Pause,
  Play,
  Plus,
  RefreshCw,
  Search,
  Settings2,
  Zap,
} from 'lucide-react'
import Badge from '../../components/ui/Badge'
import Button from '../../components/ui/Button'
import Card from '../../components/ui/Card'
import Input from '../../components/ui/Input'
import Skeleton from '../../components/ui/Skeleton'
import { useToastStore } from '../../stores/toast-store'
import {
  addToKnowledgeFrontier,
  getAdvisorPersona,
  getKnowledgeDirectives,
  getKnowledgeFrontier,
  getKnowledgeStatus,
  getRecentKnowledgeDocuments,
  pauseKnowledgeEngine,
  resumeKnowledgeEngine,
  setKnowledgeThrottle,
  triggerKnowledgeDiscovery,
  triggerKnowledgeTick,
  updateAdvisorPersona,
  updateKnowledgeDirective,
} from '../../api/admin'
import type {
  FrontierItem,
  KnowledgeDirective,
  KnowledgeDocument,
  KnowledgeStatusResponse,
} from '../../types'

function statusBadge(status: string) {
  if (['idle', 'completed', 'ok'].includes(status))
    return <Badge variant="success">{status}</Badge>
  if (['running', 'processing', 'pending'].includes(status))
    return <Badge variant="warning">{status}</Badge>
  if (['failed', 'error', 'paused'].includes(status))
    return <Badge variant="danger">{status}</Badge>
  return <Badge variant="neutral">{status}</Badge>
}

export default function AdminKnowledgePage() {
  const addToast = useToastStore(s => s.addToast)
  const qc = useQueryClient()
  const invalidate = () => {
    qc.invalidateQueries({ queryKey: ['knowledge-status'] })
    qc.invalidateQueries({ queryKey: ['knowledge-docs'] })
    qc.invalidateQueries({ queryKey: ['knowledge-frontier'] })
    qc.invalidateQueries({ queryKey: ['knowledge-directives'] })
  }

  const statusQ = useQuery<KnowledgeStatusResponse>({
    queryKey: ['knowledge-status'],
    queryFn: getKnowledgeStatus,
    refetchInterval: 5000,
  })
  const docsQ = useQuery<KnowledgeDocument[]>({
    queryKey: ['knowledge-docs'],
    queryFn: () => getRecentKnowledgeDocuments(15),
    refetchInterval: 10000,
  })
  const frontierQ = useQuery<FrontierItem[]>({
    queryKey: ['knowledge-frontier'],
    queryFn: () => getKnowledgeFrontier({ limit: 15 }),
    refetchInterval: 10000,
  })
  const directivesQ = useQuery<KnowledgeDirective[]>({
    queryKey: ['knowledge-directives'],
    queryFn: getKnowledgeDirectives,
    refetchInterval: 30000,
  })

  const tickMut = useMutation({
    mutationFn: triggerKnowledgeTick,
    onSuccess: () => { addToast('Engine tick triggered', 'success'); invalidate() },
    onError: () => addToast('Tick failed', 'error'),
  })
  const discoveryMut = useMutation({
    mutationFn: triggerKnowledgeDiscovery,
    onSuccess: () => { addToast('Discovery triggered', 'success'); invalidate() },
    onError: () => addToast('Discovery failed', 'error'),
  })
  const pauseMut = useMutation({
    mutationFn: pauseKnowledgeEngine,
    onSuccess: () => { addToast('Engine paused', 'success'); invalidate() },
  })
  const resumeMut = useMutation({
    mutationFn: resumeKnowledgeEngine,
    onSuccess: () => { addToast('Engine resumed', 'success'); invalidate() },
  })

  const [rpmInput, setRpmInput] = useState('')
  const throttleMut = useMutation({
    mutationFn: (rpm: number) => setKnowledgeThrottle(rpm),
    onSuccess: () => { addToast('RPM updated', 'success'); invalidate() },
  })

  const [addUrlInput, setAddUrlInput] = useState('')
  const addUrlMut = useMutation({
    mutationFn: (url: string) => addToKnowledgeFrontier(url),
    onSuccess: (data: { status: string }) => {
      addToast(data.status === 'added' ? 'URL added to frontier' : 'URL skipped (duplicate)', 'success')
      setAddUrlInput('')
      invalidate()
    },
    onError: () => addToast('Failed to add URL', 'error'),
  })

  const personaQ = useQuery<Record<string, unknown>>({
    queryKey: ['advisor-persona'],
    queryFn: getAdvisorPersona,
    refetchInterval: 30000,
  })

  const personaMut = useMutation({
    mutationFn: (data: Record<string, unknown>) => updateAdvisorPersona(data as Parameters<typeof updateAdvisorPersona>[0]),
    onSuccess: () => { addToast('Persona updated', 'success'); qc.invalidateQueries({ queryKey: ['advisor-persona'] }) },
    onError: () => addToast('Persona update failed', 'error'),
  })

  const toggleDirectiveMut = useMutation({
    mutationFn: ({ id, active }: { id: string; active: boolean }) =>
      updateKnowledgeDirective(id, { is_active: active }),
    onSuccess: () => { addToast('Directive updated', 'success'); invalidate() },
  })

  const engine = statusQ.data?.engine
  const knowledge = statusQ.data?.knowledge
  const frontier = statusQ.data?.frontier

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Knowledge Engine</h1>
          <p className="text-sm text-gray-500 mt-1">
            Perpetual learning loop — ingests, understands, and links public knowledge
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            size="sm"
            variant="secondary"
            onClick={() => invalidate()}
          >
            <RefreshCw size={14} className="mr-1" /> Refresh
          </Button>
        </div>
      </div>

      {/* === Engine Status Strip === */}
      {statusQ.isLoading ? (
        <Skeleton className="h-24" />
      ) : engine ? (
        <Card className="p-4">
          <div className="flex flex-wrap items-center gap-6">
            <div className="flex items-center gap-2">
              <Brain size={20} className="text-indigo-600" />
              <span className="font-semibold">Status:</span>
              {statusBadge(engine.paused ? 'paused' : engine.status)}
            </div>
            <div className="flex items-center gap-2">
              <Zap size={16} className="text-amber-500" />
              <span className="text-sm">
                <span className="font-medium">{engine.rpm}</span> RPM
              </span>
            </div>
            <div className="text-sm text-gray-600">
              Processed: <span className="font-medium">{engine.total_processed}</span>
            </div>
            <div className="text-sm text-gray-600">
              Errors: <span className="font-medium text-red-600">{engine.total_errors}</span>
            </div>
            <div className="text-sm text-gray-600">
              Discovered: <span className="font-medium text-blue-600">{engine.total_discovered}</span>
            </div>
            {engine.last_tick_at && (
              <div className="text-xs text-gray-400 flex items-center gap-1">
                <Clock size={12} />
                Last tick: {new Date(engine.last_tick_at).toLocaleTimeString()}
              </div>
            )}
            {engine.current_url && (
              <div className="text-xs text-indigo-500 truncate max-w-xs">
                Processing: {engine.current_url}
              </div>
            )}
          </div>
        </Card>
      ) : null}

      {/* === Controls === */}
      <Card className="p-4">
        <h2 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
          <Settings2 size={16} /> Engine Controls
        </h2>
        <div className="flex flex-wrap items-end gap-4">
          {engine?.paused ? (
            <Button size="sm" onClick={() => resumeMut.mutate()} disabled={resumeMut.isPending}>
              <Play size={14} className="mr-1" /> Resume
            </Button>
          ) : (
            <Button size="sm" variant="secondary" onClick={() => pauseMut.mutate()} disabled={pauseMut.isPending}>
              <Pause size={14} className="mr-1" /> Pause
            </Button>
          )}
          <Button size="sm" onClick={() => tickMut.mutate()} disabled={tickMut.isPending}>
            <Zap size={14} className="mr-1" /> Run Tick
          </Button>
          <Button size="sm" variant="secondary" onClick={() => discoveryMut.mutate()} disabled={discoveryMut.isPending}>
            <Search size={14} className="mr-1" /> Run Discovery
          </Button>
          <div className="flex items-end gap-1">
            <div>
              <label className="text-xs text-gray-500 block mb-1">RPM</label>
              <Input
                value={rpmInput}
                onChange={e => setRpmInput(e.target.value)}
                placeholder={String(engine?.rpm ?? 10)}
                className="w-20"
              />
            </div>
            <Button
              size="sm"
              variant="secondary"
              disabled={!rpmInput || throttleMut.isPending}
              onClick={() => {
                const v = parseInt(rpmInput, 10)
                if (v >= 1 && v <= 100) throttleMut.mutate(v)
              }}
            >
              Set
            </Button>
          </div>
          <div className="flex items-end gap-1">
            <div>
              <label className="text-xs text-gray-500 block mb-1">Add URL</label>
              <Input
                value={addUrlInput}
                onChange={e => setAddUrlInput(e.target.value)}
                placeholder="https://..."
                className="w-72"
              />
            </div>
            <Button
              size="sm"
              disabled={!addUrlInput || addUrlMut.isPending}
              onClick={() => addUrlMut.mutate(addUrlInput)}
            >
              <Plus size={14} className="mr-1" /> Add
            </Button>
          </div>
        </div>
      </Card>

      {/* === Knowledge Stats + Frontier Stats === */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="p-4 text-center">
          <div className="text-3xl font-bold text-indigo-600">{knowledge?.total_documents ?? '—'}</div>
          <div className="text-xs text-gray-500 mt-1">Total Documents</div>
        </Card>
        <Card className="p-4 text-center">
          <div className="text-3xl font-bold text-green-600">{knowledge?.active_documents ?? '—'}</div>
          <div className="text-xs text-gray-500 mt-1">Active & Completed</div>
        </Card>
        <Card className="p-4 text-center">
          <div className="text-3xl font-bold text-blue-600">{frontier?.pending ?? '—'}</div>
          <div className="text-xs text-gray-500 mt-1">Frontier Pending</div>
        </Card>
        <Card className="p-4 text-center">
          <div className="text-3xl font-bold text-red-500">{frontier?.failed ?? '—'}</div>
          <div className="text-xs text-gray-500 mt-1">Frontier Failed</div>
        </Card>
      </div>

      {/* === Content Breakdown === */}
      {knowledge && (Object.keys(knowledge.by_format).length > 0 || Object.keys(knowledge.by_type).length > 0) && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {Object.keys(knowledge.by_format).length > 0 && (
            <Card className="p-4">
              <h3 className="text-sm font-semibold text-gray-700 mb-2">By Format</h3>
              <div className="space-y-1">
                {Object.entries(knowledge.by_format).sort((a, b) => b[1] - a[1]).map(([fmt, count]) => (
                  <div key={fmt} className="flex justify-between text-sm">
                    <span className="text-gray-600">{fmt}</span>
                    <span className="font-medium">{count}</span>
                  </div>
                ))}
              </div>
            </Card>
          )}
          {Object.keys(knowledge.by_type).length > 0 && (
            <Card className="p-4">
              <h3 className="text-sm font-semibold text-gray-700 mb-2">By Type</h3>
              <div className="space-y-1">
                {Object.entries(knowledge.by_type).sort((a, b) => b[1] - a[1]).map(([typ, count]) => (
                  <div key={typ} className="flex justify-between text-sm">
                    <span className="text-gray-600">{typ}</span>
                    <span className="font-medium">{count}</span>
                  </div>
                ))}
              </div>
            </Card>
          )}
        </div>
      )}

      {/* === Directives === */}
      <Card className="p-4">
        <h2 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
          <Settings2 size={16} /> Steering Directives
        </h2>
        {directivesQ.isLoading ? (
          <Skeleton className="h-16" />
        ) : (directivesQ.data ?? []).length === 0 ? (
          <p className="text-sm text-gray-400">No directives configured</p>
        ) : (
          <div className="space-y-2">
            {(directivesQ.data ?? []).map((d: KnowledgeDirective) => (
              <div key={d.id} className="flex items-center justify-between border rounded-lg px-3 py-2 text-sm">
                <div className="flex items-center gap-3">
                  <Badge variant={d.is_active ? 'success' : 'neutral'}>
                    {d.is_active ? 'active' : 'off'}
                  </Badge>
                  <span className="font-medium">{d.directive_type}:{d.directive_key}</span>
                  {d.description && (
                    <span className="text-gray-400 text-xs truncate max-w-xs">{d.description}</span>
                  )}
                </div>
                <Button
                  size="sm"
                  variant="secondary"
                  onClick={() => toggleDirectiveMut.mutate({ id: d.id, active: !d.is_active })}
                  disabled={toggleDirectiveMut.isPending}
                >
                  {d.is_active ? 'Disable' : 'Enable'}
                </Button>
              </div>
            ))}
          </div>
        )}
      </Card>

      {/* === Recent Documents === */}
      {/* === Advisor Persona === */}
      <Card className="p-4">
        <h2 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
          <Brain size={16} /> Advisor Persona
        </h2>
        {personaQ.isLoading ? (
          <Skeleton className="h-32" />
        ) : personaQ.data && !('status' in personaQ.data && personaQ.data.status === 'no_active_persona') ? (
          <div className="space-y-3">
            {[
              { key: 'warmth', label: 'Warmth', desc: 'warm vs professional' },
              { key: 'directness', label: 'Directness', desc: 'direct vs gentle' },
              { key: 'formality', label: 'Formality', desc: 'casual vs formal' },
              { key: 'challenge_level', label: 'Challenge', desc: 'supportive vs challenging' },
              { key: 'data_reference_frequency', label: 'Data Usage', desc: 'human vs data-driven' },
              { key: 'humor', label: 'Humor', desc: 'serious vs playful' },
              { key: 'proactivity', label: 'Proactivity', desc: 'reactive vs proactive' },
              { key: 'empathy_depth', label: 'Empathy', desc: 'surface vs deep' },
            ].map(({ key, label, desc }) => (
              <div key={key} className="flex items-center gap-3">
                <label className="w-28 text-sm text-gray-600">{label}</label>
                <input
                  type="range"
                  min={0}
                  max={100}
                  value={Number(personaQ.data?.[key] ?? 50)}
                  onChange={e => personaMut.mutate({ [key]: parseInt(e.target.value, 10) })}
                  className="flex-1 h-2 rounded-lg appearance-none bg-gray-200 cursor-pointer"
                />
                <span className="w-8 text-xs text-gray-500 text-right">
                  {String(personaQ.data?.[key] ?? 50)}
                </span>
                <span className="text-xs text-gray-400 w-32 truncate">{desc}</span>
              </div>
            ))}
            <div className="mt-4">
              <label className="text-sm text-gray-600 block mb-1">Custom Instructions</label>
              <textarea
                className="w-full border rounded-lg p-2 text-sm h-20 resize-none"
                defaultValue={String(personaQ.data?.custom_instructions ?? '')}
                onBlur={e => {
                  if (e.target.value !== personaQ.data?.custom_instructions) {
                    personaMut.mutate({ custom_instructions: e.target.value })
                  }
                }}
                placeholder="e.g., Always mention scholarships for international students..."
              />
            </div>
          </div>
        ) : (
          <p className="text-sm text-gray-400">No active persona configured</p>
        )}
      </Card>

      <Card className="p-4">
        <h2 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
          <FileText size={16} /> Recent Knowledge Documents
        </h2>
        {docsQ.isLoading ? (
          <Skeleton className="h-32" />
        ) : (docsQ.data ?? []).length === 0 ? (
          <p className="text-sm text-gray-400">No documents ingested yet. Run a tick or wait for the scheduler.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-gray-500 border-b">
                  <th className="pb-2 pr-4">Title</th>
                  <th className="pb-2 pr-4">Format</th>
                  <th className="pb-2 pr-4">Type</th>
                  <th className="pb-2 pr-4">Quality</th>
                  <th className="pb-2 pr-4">Status</th>
                  <th className="pb-2">Time</th>
                </tr>
              </thead>
              <tbody>
                {(docsQ.data ?? []).map((doc: KnowledgeDocument) => (
                  <tr key={doc.id} className="border-b last:border-0">
                    <td className="py-2 pr-4 max-w-xs truncate">
                      {doc.source_url ? (
                        <a
                          href={doc.source_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-indigo-600 hover:underline flex items-center gap-1"
                        >
                          {doc.title || doc.source_domain || 'Untitled'}
                          <ExternalLink size={10} />
                        </a>
                      ) : (
                        doc.title || 'Untitled'
                      )}
                    </td>
                    <td className="py-2 pr-4">
                      <Badge variant="neutral">{doc.content_format}</Badge>
                    </td>
                    <td className="py-2 pr-4 text-gray-500">{doc.content_type || '—'}</td>
                    <td className="py-2 pr-4">
                      {doc.quality_score != null ? (
                        <span className={doc.quality_score >= 0.7 ? 'text-green-600' : doc.quality_score >= 0.4 ? 'text-amber-600' : 'text-red-500'}>
                          {(doc.quality_score * 100).toFixed(0)}%
                        </span>
                      ) : '—'}
                    </td>
                    <td className="py-2 pr-4">{statusBadge(doc.processing_status)}</td>
                    <td className="py-2 text-gray-400 text-xs">
                      {doc.created_at ? new Date(doc.created_at).toLocaleString() : '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {/* === Frontier Queue === */}
      <Card className="p-4">
        <h2 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
          <Globe size={16} /> Crawl Frontier
        </h2>
        {frontierQ.isLoading ? (
          <Skeleton className="h-32" />
        ) : (frontierQ.data ?? []).length === 0 ? (
          <p className="text-sm text-gray-400">Frontier is empty. Run discovery or add URLs manually.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-gray-500 border-b">
                  <th className="pb-2 pr-4">URL</th>
                  <th className="pb-2 pr-4">Domain</th>
                  <th className="pb-2 pr-4">Priority</th>
                  <th className="pb-2 pr-4">Status</th>
                  <th className="pb-2 pr-4">Crawls</th>
                  <th className="pb-2">Source</th>
                </tr>
              </thead>
              <tbody>
                {(frontierQ.data ?? []).map((f: FrontierItem) => (
                  <tr key={f.id} className="border-b last:border-0">
                    <td className="py-2 pr-4 max-w-sm truncate">
                      <a
                        href={f.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-indigo-600 hover:underline flex items-center gap-1"
                      >
                        {f.url}
                        <ExternalLink size={10} />
                      </a>
                    </td>
                    <td className="py-2 pr-4 text-gray-500">{f.domain}</td>
                    <td className="py-2 pr-4 font-medium">{f.priority}</td>
                    <td className="py-2 pr-4">{statusBadge(f.status)}</td>
                    <td className="py-2 pr-4">{f.crawl_count}</td>
                    <td className="py-2 text-gray-400 text-xs">{f.discovery_method || '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {engine?.last_error && (
        <Card className="p-4 border-red-200 bg-red-50">
          <h3 className="text-sm font-semibold text-red-700 mb-1">Last Error</h3>
          <p className="text-sm text-red-600 font-mono">{engine.last_error}</p>
        </Card>
      )}
    </div>
  )
}
