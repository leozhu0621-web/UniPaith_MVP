import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Shield, ShieldAlert, AlertTriangle, ExternalLink, ClipboardCheck } from 'lucide-react'
import { getIntegritySignals, resolveIntegritySignal } from '../../api/reviews'
import Card from '../../components/ui/Card'
import Badge from '../../components/ui/Badge'
import Button from '../../components/ui/Button'
import Modal from '../../components/ui/Modal'
import Textarea from '../../components/ui/Textarea'
import Tabs from '../../components/ui/Tabs'
import EmptyState from '../../components/ui/EmptyState'
import Skeleton from '../../components/ui/Skeleton'
import InstitutionPageHeader from '../../components/institution/InstitutionPageHeader'
import { showToast } from '../../stores/toast-store'
import { formatRelative } from '../../utils/format'
import type { IntegritySignal, IntegrityResolution } from '../../types'

const SEVERITY_BADGE: Record<string, 'danger' | 'warning' | 'neutral'> = {
  high: 'danger',
  medium: 'warning',
  low: 'neutral',
}

// Spec 31 §6 — the three resolution outcomes.
const RESOLUTIONS: { id: IntegrityResolution; label: string; desc: string }[] = [
  { id: 'acceptable', label: 'Acceptable', desc: 'Reviewed — no integrity concern. Clear the flag.' },
  { id: 'requires_clarification', label: 'Requires clarification', desc: 'Follow up with the applicant before deciding.' },
  { id: 'reject_application', label: 'Reject application', desc: 'Recommend rejection (advisory — release the decision separately).' },
]

const SIGNAL_LABELS: Record<string, string> = {
  duplicate_submission: 'Duplicate submission',
  credential_mismatch: 'Credential mismatch',
  essay_authenticity: 'Essay authenticity',
  incomplete_profile: 'Incomplete profile',
}

function EvidenceChips({ signal }: { signal: IntegritySignal }) {
  const ev = signal.evidence
  if (!ev) return null
  const chips: string[] = []
  // Authenticity confidence band (spec §6) — surfaced first when present.
  if (ev.risk_band) chips.push(`Authenticity risk: ${String(ev.risk_band)}`)
  if (ev.confidence != null) chips.push(`Confidence: ${Math.round(Number(ev.confidence) * 100)}%`)
  if (ev.gpa) chips.push(`GPA: ${String(ev.gpa)}`)
  if (ev.score && ev.test_type) chips.push(`${String(ev.test_type)}: ${String(ev.score)}`)
  if (ev.valid_range) chips.push(`Valid: ${String(ev.valid_range)}`)
  if (Array.isArray(ev.signals) && ev.signals.length) chips.push(`Tells: ${ev.signals.join(', ')}`)
  if (!chips.length) return null
  return (
    <div className="mt-2 flex flex-wrap gap-1.5">
      {chips.map((c, i) => (
        <span key={i} className="rounded bg-muted px-1.5 py-0.5 text-xs text-muted-foreground">{c}</span>
      ))}
    </div>
  )
}

export default function IntegrityQueuePage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [activeTab, setActiveTab] = useState('open')
  const [selected, setSelected] = useState<IntegritySignal | null>(null)
  const [resolution, setResolution] = useState<IntegrityResolution>('acceptable')
  const [notes, setNotes] = useState('')

  const tabs = [
    { id: 'open', label: 'Open' },
    { id: 'resolved', label: 'Resolved' },
    { id: 'all', label: 'All' },
  ]

  const statusFilter = activeTab === 'all' ? undefined : activeTab
  const signalsQ = useQuery({
    queryKey: ['integrity-signals', statusFilter],
    queryFn: () => getIntegritySignals(undefined, statusFilter),
  })
  const signals: IntegritySignal[] = Array.isArray(signalsQ.data) ? signalsQ.data : []

  const resolveMut = useMutation({
    mutationFn: (p: { id: string; resolution: IntegrityResolution; notes?: string }) =>
      resolveIntegritySignal(p.id, p.resolution, p.notes),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['integrity-signals'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard-integrity'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard-summary'] })
      showToast('Integrity signal resolved', 'success')
      setSelected(null)
      setNotes('')
      setResolution('acceptable')
    },
    onError: () => showToast('Failed to resolve signal', 'error'),
  })

  const openResolve = (sig: IntegritySignal) => {
    setSelected(sig)
    setResolution('acceptable')
    setNotes(sig.resolution_notes || '')
  }

  const openCount = signals.filter(s => s.status === 'open').length
  const highCount = signals.filter(s => s.status === 'open' && s.severity === 'high').length

  return (
    <div className="p-6 space-y-4">
      <InstitutionPageHeader
        title="Integrity Signals"
        description="Review document-authenticity, duplicate-identity, and anomaly flags. Resolve each as acceptable, needing clarification, or recommending rejection."
      />

      {signals.length > 0 && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          <Card className="p-3">
            <p className="text-xs text-gray-500">Open</p>
            <p className="text-xl font-bold text-gray-900">{openCount}</p>
          </Card>
          <Card className="p-3 border-amber-200">
            <p className="text-xs text-amber-600">High severity</p>
            <p className="text-xl font-bold text-amber-700">{highCount}</p>
          </Card>
        </div>
      )}

      <Tabs tabs={tabs} activeTab={activeTab} onChange={setActiveTab} />

      {signalsQ.isLoading ? (
        <div className="space-y-3">{Array.from({ length: 3 }).map((_, i) => <Skeleton key={i} className="h-28" />)}</div>
      ) : signals.length === 0 ? (
        <EmptyState
          icon={<Shield size={40} />}
          title={activeTab === 'open' ? 'No open integrity signals' : 'No signals'}
          description="Integrity flags surface here as applications are scanned. All clear for now."
        />
      ) : (
        <div className="space-y-2">
          {signals.map(sig => (
            <Card key={sig.id} className="p-4">
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    {sig.severity === 'high'
                      ? <ShieldAlert size={16} className="text-red-600 shrink-0" />
                      : <AlertTriangle size={16} className="text-amber-600 shrink-0" />}
                    <h3 className="text-sm font-semibold text-gray-900">{sig.title}</h3>
                    <Badge variant={SEVERITY_BADGE[sig.severity] ?? 'neutral'}>{sig.severity}</Badge>
                    <Badge variant="info">{SIGNAL_LABELS[sig.signal_type] ?? sig.signal_type.replace(/_/g, ' ')}</Badge>
                    {sig.status === 'resolved' && (
                      <Badge variant="success">
                        Resolved{sig.resolution ? ` · ${sig.resolution.replace(/_/g, ' ')}` : ''}
                      </Badge>
                    )}
                  </div>
                  <p className="mt-1 text-sm text-gray-600">{sig.description}</p>
                  <EvidenceChips signal={sig} />
                  <div className="mt-2 flex items-center gap-3 text-xs text-gray-400">
                    <button
                      onClick={() => navigate(`/i/pipeline/${sig.application_id}`)}
                      className="inline-flex items-center gap-1 text-secondary hover:underline"
                    >
                      <ExternalLink size={12} /> View applicant
                    </button>
                    <span>Flagged {formatRelative(sig.created_at)}</span>
                  </div>
                </div>
                {sig.status === 'open' && (
                  <Button size="sm" variant="secondary" onClick={() => openResolve(sig)} className="shrink-0 flex items-center gap-1">
                    <ClipboardCheck size={13} /> Resolve
                  </Button>
                )}
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Resolve modal — Spec 31 §6 three-outcome workflow. */}
      <Modal isOpen={!!selected} onClose={() => setSelected(null)} title="Resolve integrity signal">
        {selected && (
          <div className="space-y-4">
            <Card className="p-3 bg-gray-50">
              <p className="text-sm font-medium text-gray-900">{selected.title}</p>
              <p className="mt-1 text-xs text-gray-600">{selected.description}</p>
            </Card>

            <div className="space-y-2">
              {RESOLUTIONS.map(r => (
                <button
                  key={r.id}
                  onClick={() => setResolution(r.id)}
                  className={`flex w-full flex-col items-start rounded-lg border px-3 py-2 text-left transition-colors ${
                    resolution === r.id ? 'border-secondary bg-secondary/5 ring-1 ring-secondary' : 'border-border hover:bg-muted'
                  }`}
                >
                  <span className="text-sm font-medium text-foreground">{r.label}</span>
                  <span className="text-xs text-muted-foreground">{r.desc}</span>
                </button>
              ))}
            </div>

            <Textarea
              label="Resolution notes (optional)"
              value={notes}
              onChange={e => setNotes(e.target.value)}
              rows={3}
              placeholder="Add context for the audit trail…"
            />

            <div className="flex justify-end gap-2">
              <Button variant="ghost" onClick={() => setSelected(null)}>Cancel</Button>
              <Button
                onClick={() => resolveMut.mutate({ id: selected.id, resolution, notes: notes || undefined })}
                disabled={resolveMut.isPending}
              >
                {resolveMut.isPending ? 'Resolving…' : 'Confirm resolution'}
              </Button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  )
}
