/**
 * Profile → Data Rights tab (spec 10 §16 / 43 §8).
 * 4 consent levers (incl. training) with change history · portable export
 * (JSON / PDF / Common App / Coalition / LinkedIn URL) · access log · danger zone.
 */
import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { AlertTriangle, Download, FileJson, FileText, Link2, ShieldCheck } from 'lucide-react'

import {
  createOnlinePresence,
  exportProfileExternal,
  exportProfileJson,
  exportProfilePdf,
  getAccessLog,
  getDataRights,
  upsertDataRights,
} from '../../../api/students'
import Button from '../../../components/ui/Button'
import Card from '../../../components/ui/Card'
import Modal from '../../../components/ui/Modal'
import { SkeletonCard } from '../../../components/ui/Skeleton'
import { showToast } from '../../../stores/toast-store'
import type { AccessLogEntry, StudentDataConsent } from '../../../types'
import { EmptyHint, relativeTime, SectionCard } from './_shared'

type LeverKey = 'consent_matching' | 'consent_outreach' | 'consent_research' | 'consent_training'

const LEVERS: { key: LeverKey; title: string; desc: string }[] = [
  { key: 'consent_matching', title: 'AI matching & personalization', desc: 'Use my profile to power matches and AI rationales. Turning this off stops all AI personalization.' },
  { key: 'consent_outreach', title: 'Institution outreach', desc: 'Let institutions send me campaign messages.' },
  { key: 'consent_research', title: 'Analytics & product improvement', desc: 'Include de-identified, aggregated activity in cross-cohort insights.' },
  { key: 'consent_training', title: 'Model training', desc: 'Include my data in a future UniPaith model-training corpus. Off by default.' },
]

function Toggle({ checked, onChange, disabled }: { checked: boolean; onChange: (v: boolean) => void; disabled?: boolean }) {
  return (
    <button
      role="switch"
      aria-checked={checked}
      disabled={disabled}
      onClick={() => onChange(!checked)}
      className={`relative w-11 h-6 rounded-full transition-colors shrink-0 ${checked ? 'bg-cobalt' : 'bg-stone'} ${disabled ? 'opacity-50' : ''}`}
    >
      <span className={`absolute top-0.5 left-0.5 w-5 h-5 rounded-full bg-white shadow-sm transition-transform ${checked ? 'translate-x-5' : ''}`} />
    </button>
  )
}

function downloadJson(data: unknown, filename: string) {
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}

export default function DataTab() {
  const qc = useQueryClient()
  const { data: consent, isLoading } = useQuery<StudentDataConsent | null>({ queryKey: ['data-rights'], queryFn: getDataRights, retry: false })
  const { data: accessLog } = useQuery<AccessLogEntry[]>({ queryKey: ['access-log'], queryFn: getAccessLog, retry: false })
  const [showHistory, setShowHistory] = useState<LeverKey | null>(null)
  const [confirmDelete, setConfirmDelete] = useState(false)
  const [linkedin, setLinkedin] = useState('')

  const mut = useMutation({
    mutationFn: upsertDataRights,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['data-rights'] })
      qc.invalidateQueries({ queryKey: ['peer-comparison'] })
      showToast('Saved', 'success')
    },
    onError: () => showToast("Something didn't work. Try again.", 'error'),
  })

  const deleteMut = useMutation({
    mutationFn: () => upsertDataRights({ deletion_requested: true }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['data-rights'] })
      setConfirmDelete(false)
      showToast('Deletion requested', 'success')
    },
    onError: () => showToast("Something didn't work. Try again.", 'error'),
  })

  const linkedinMut = useMutation({
    mutationFn: (url: string) => createOnlinePresence({ platform_type: 'linkedin', url, display_name: 'LinkedIn' }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['profile'] })
      setLinkedin('')
      showToast('LinkedIn saved to your profile', 'success')
    },
    onError: () => showToast("Couldn't save that link. Check the URL.", 'error'),
  })

  const [exporting, setExporting] = useState<string | null>(null)
  const runExport = async (kind: 'json' | 'pdf' | 'commonapp' | 'coalition') => {
    setExporting(kind)
    try {
      if (kind === 'json') await exportProfileJson()
      else if (kind === 'pdf') await exportProfilePdf()
      else {
        const data = await exportProfileExternal(kind)
        downloadJson(data, `unipaith-${kind}.json`)
      }
      showToast('Export ready', 'success')
    } catch {
      showToast("Export didn't work. Try again.", 'error')
    } finally {
      setExporting(null)
    }
  }

  const lastChange = (key: LeverKey) => {
    const log = consent?.consent_change_log ?? []
    const entries = log.filter(e => e.lever === key)
    return entries.length ? entries[entries.length - 1].at : null
  }
  const leverValue = (key: LeverKey): boolean => {
    if (consent) return Boolean(consent[key])
    // No consent row yet → backend defaults (matching/outreach/research on, training off).
    return key !== 'consent_training'
  }

  if (isLoading) return <div className="space-y-4"><SkeletonCard /><SkeletonCard /></div>

  const deletionRequested = consent?.deletion_requested
  const log = Array.isArray(accessLog) ? accessLog : []

  return (
    <div className="space-y-6">
      {/* Consent levers */}
      <SectionCard title="Consent" icon={ShieldCheck}>
        <div className="space-y-4">
          {LEVERS.map(lever => {
            const changed = lastChange(lever.key)
            const historyEntries = (consent?.consent_change_log ?? []).filter(e => e.lever === lever.key)
            return (
              <div key={lever.key} className="flex items-start justify-between gap-4 border-b border-divider pb-4 last:border-0 last:pb-0">
                <div className="min-w-0">
                  <p className="text-sm font-medium text-charcoal">{lever.title}</p>
                  <p className="text-xs text-slate mt-0.5">{lever.desc}</p>
                  <p className="text-xs text-slate mt-1">
                    {changed ? `Last changed ${relativeTime(changed)}.` : 'Not changed yet.'}
                    {historyEntries.length > 0 && (
                      <button onClick={() => setShowHistory(showHistory === lever.key ? null : lever.key)} className="text-cobalt ml-1 story-link">
                        Change history
                      </button>
                    )}
                  </p>
                  {showHistory === lever.key && historyEntries.length > 0 && (
                    <ul className="mt-1 space-y-0.5">
                      {historyEntries.slice().reverse().map((e, i) => (
                        <li key={i} className="text-xs text-slate">{e.value ? 'Enabled' : 'Disabled'} · {relativeTime(e.at)}</li>
                      ))}
                    </ul>
                  )}
                </div>
                <Toggle
                  checked={leverValue(lever.key)}
                  disabled={mut.isPending}
                  onChange={v => mut.mutate({ [lever.key]: v })}
                />
              </div>
            )
          })}
        </div>
      </SectionCard>

      {/* Portable export */}
      <SectionCard title="Export your data" icon={Download}>
        <p className="text-xs text-slate mb-3">Download everything we store about you, or carry it into another platform.</p>
        <div className="flex flex-wrap gap-2">
          <Button size="sm" variant="tertiary" loading={exporting === 'json'} onClick={() => runExport('json')}><FileJson size={14} className="mr-1" /> JSON</Button>
          <Button size="sm" variant="tertiary" loading={exporting === 'pdf'} onClick={() => runExport('pdf')}><FileText size={14} className="mr-1" /> PDF</Button>
          <Button size="sm" variant="tertiary" loading={exporting === 'commonapp'} onClick={() => runExport('commonapp')}>Common App</Button>
          <Button size="sm" variant="tertiary" loading={exporting === 'coalition'} onClick={() => runExport('coalition')}>Coalition</Button>
        </div>
        <div className="mt-4 pt-4 border-t border-divider">
          <p className="text-sm font-medium text-charcoal flex items-center gap-1.5"><Link2 size={14} className="text-cobalt" /> Import from LinkedIn</p>
          <p className="text-xs text-slate mt-0.5 mb-2">Save your LinkedIn URL now. Full work/education sync is coming soon.</p>
          <div className="flex gap-2">
            <input
              value={linkedin}
              onChange={e => setLinkedin(e.target.value)}
              placeholder="https://linkedin.com/in/you"
              className="flex-1 text-sm border border-border rounded-lg px-3 py-1.5 bg-card text-charcoal"
            />
            <Button size="sm" variant="secondary" loading={linkedinMut.isPending} disabled={!linkedin.trim()} onClick={() => linkedinMut.mutate(linkedin.trim())}>Save</Button>
          </div>
        </div>
      </SectionCard>

      {/* Access log */}
      <SectionCard title="Who has access" icon={ShieldCheck}>
        {log.length === 0 ? (
          <EmptyHint>No access yet. When you apply, the institution gains access to your profile and it'll appear here.</EmptyHint>
        ) : (
          <div className="space-y-2">
            {log.map((e, i) => (
              <div key={i} className="flex justify-between items-center gap-3 text-sm border-b border-divider pb-2 last:border-0">
                <div className="min-w-0">
                  <p className="text-charcoal font-medium truncate">{e.viewer}</p>
                  <p className="text-xs text-slate">{e.context ? `${e.context} · ` : ''}{e.fields_accessed}</p>
                </div>
                <span className="text-xs text-slate shrink-0">{e.accessed_at ? relativeTime(e.accessed_at) : ''}</span>
              </div>
            ))}
          </div>
        )}
      </SectionCard>

      {/* Danger zone */}
      <Card className="p-5 border-error/40">
        <div className="flex items-center gap-2 mb-2">
          <AlertTriangle size={16} className="text-error" />
          <h3 className="font-semibold text-charcoal">Danger zone</h3>
        </div>
        {deletionRequested ? (
          <div className="flex items-center justify-between gap-3">
            <p className="text-sm text-error">Deletion requested. Your account and data will be permanently deleted after a 30-day grace period.</p>
            <Button size="sm" variant="tertiary" loading={mut.isPending} onClick={() => mut.mutate({ deletion_requested: false })}>Cancel</Button>
          </div>
        ) : (
          <div className="flex items-center justify-between gap-3">
            <p className="text-sm text-slate">Permanently delete your account and all profile data.</p>
            <Button size="sm" variant="danger" onClick={() => setConfirmDelete(true)}>Delete account</Button>
          </div>
        )}
      </Card>

      <Modal isOpen={confirmDelete} onClose={() => setConfirmDelete(false)} title="Delete account" size="sm">
        <p className="text-sm text-charcoal mb-4">
          Are you sure? Your account and all profile data will be permanently deleted after a 30-day grace period.
        </p>
        <div className="flex justify-end gap-2">
          <Button variant="tertiary" onClick={() => setConfirmDelete(false)}>Cancel</Button>
          <Button variant="danger" loading={deleteMut.isPending} onClick={() => deleteMut.mutate()}>Delete account</Button>
        </div>
      </Modal>
    </div>
  )
}
