import { useEffect, useMemo, useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { batchReleaseDecisionV2 } from '../../../api/applications-admin'
import { getTemplates, previewTemplate } from '../../../api/institutions'
import Modal from '../../../components/ui/Modal'
import Button from '../../../components/ui/Button'
import Select from '../../../components/ui/Select'
import Input from '../../../components/ui/Input'
import Badge from '../../../components/ui/Badge'
import { showToast } from '../../../stores/toast-store'
import type { Application, BatchReleaseItem, InstitutionDecision, ReleaseOfferTerms } from '../../../types'
import {
  INSTITUTION_DECISIONS,
  decisionLabel,
  formatOfferTermsSummary,
  isOfferDecision,
} from './decisionUtils'

const DECISION_TONE: Record<InstitutionDecision, 'success' | 'info' | 'warning' | 'neutral' | 'danger'> = {
  admitted: 'success',
  conditional_admission: 'info',
  waitlisted: 'warning',
  deferred: 'neutral',
  rejected: 'danger',
}

const applicantLabel = (a: Application) =>
  a.student_name ?? `Applicant ${a.student_id.slice(0, 8)}`

/** Batch decision release (spec 34 §5): confirm per applicant, standard offer template, progress while releasing. */
export default function BatchReleaseModal({
  isOpen,
  onClose,
  selectedApps,
  onDone,
}: {
  isOpen: boolean
  onClose: () => void
  selectedApps: Application[]
  onDone: () => void
}) {
  const [step, setStep] = useState<'configure' | 'confirm' | 'done'>('configure')
  const [bulk, setBulk] = useState<InstitutionDecision>('admitted')
  const [perApp, setPerApp] = useState<Record<string, InstitutionDecision>>({})
  const [scholarship, setScholarship] = useState('')
  const [deadline, setDeadline] = useState('')
  const [templateId, setTemplateId] = useState('')
  const [templateBody, setTemplateBody] = useState('')
  const [releaseProgress, setReleaseProgress] = useState(0)
  const [result, setResult] = useState<{ success_count: number; failed_count: number } | null>(null)

  const templatesQ = useQuery({
    queryKey: ['templates', 'offer_notice'],
    queryFn: () => getTemplates('offer_notice'),
    enabled: isOpen,
  })
  const offerTemplates = templatesQ.data ?? []

  useEffect(() => {
    if (!isOpen) {
      setStep('configure')
      setPerApp({})
      setResult(null)
      setReleaseProgress(0)
      setTemplateId('')
      setTemplateBody('')
    }
  }, [isOpen])

  useEffect(() => {
    if (!templateId || selectedApps.length === 0) {
      setTemplateBody('')
      return
    }
    let cancelled = false
    previewTemplate(templateId, selectedApps[0].id)
      .then(p => {
        if (!cancelled) setTemplateBody(p.rendered_body)
      })
      .catch(() => {
        if (!cancelled) setTemplateBody('')
      })
    return () => { cancelled = true }
  }, [templateId, selectedApps])

  const decisionFor = (id: string): InstitutionDecision => perApp[id] ?? bulk
  const admitCount = useMemo(
    () => selectedApps.filter(a => isOfferDecision(decisionFor(a.id))).length,
    [selectedApps, perApp, bulk],
  )

  const standardOffer = useMemo((): ReleaseOfferTerms | null => {
    if (!scholarship && !deadline) return null
    return {
      scholarship_amount: scholarship ? Number(scholarship) : null,
      response_deadline: deadline || null,
    }
  }, [scholarship, deadline])

  const releaseMut = useMutation({
    mutationFn: async () => {
      const offer = standardOffer
      const items: BatchReleaseItem[] = selectedApps.map(a => {
        const decision = decisionFor(a.id)
        const isOffer = isOfferDecision(decision)
        return {
          application_id: a.id,
          decision,
          offer: isOffer ? offer : null,
          message: isOffer && templateBody.trim() ? templateBody.trim() : null,
        }
      })
      setReleaseProgress(15)
      const data = await batchReleaseDecisionV2(items)
      setReleaseProgress(100)
      return data
    },
    onSuccess: data => {
      setResult({ success_count: data.success_count, failed_count: data.failed_count })
      setStep('done')
      showToast(
        `${data.success_count} released` + (data.failed_count ? `, ${data.failed_count} failed` : ''),
        data.failed_count ? 'warning' : 'success',
      )
      onDone()
    },
    onError: () => {
      setReleaseProgress(0)
      showToast('Batch release failed', 'error')
    },
  })

  const close = () => {
    setResult(null)
    setPerApp({})
    setStep('configure')
    onClose()
  }

  const templateOptions = [
    { value: '', label: 'No template (standard notice)' },
    ...offerTemplates.map(t => ({ value: t.id, label: t.name })),
  ]

  return (
    <Modal isOpen={isOpen} onClose={close} title="Release decisions" size="lg">
      <div className="space-y-4">
        {step === 'configure' && !result && (
          <>
            <p className="text-sm text-gray-600">
              Confirm a decision for each applicant. Offer terms apply to admits and conditional admits.
            </p>
            <div className="flex flex-wrap items-end gap-3">
              <Select
                label="Decision for all"
                options={INSTITUTION_DECISIONS.map(d => ({ value: d.value, label: d.label }))}
                value={bulk}
                onChange={e => setBulk(e.target.value as InstitutionDecision)}
                className="w-48"
              />
              <p className="text-xs text-gray-500 pb-2">Override individuals below.</p>
            </div>

            <div className="rounded-lg border border-border p-3 space-y-3">
              <p className="text-xs font-medium text-gray-500">
                Standard offer template — applied to {admitCount} admit{admitCount === 1 ? '' : 's'}
              </p>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <Input label="Scholarship ($)" type="number" value={scholarship} onChange={e => setScholarship(e.target.value)} />
                <Input label="Response deadline" type="date" value={deadline} onChange={e => setDeadline(e.target.value)} />
              </div>
              <Select
                label="Offer letter template"
                options={templateOptions}
                value={templateId}
                onChange={e => setTemplateId(e.target.value)}
              />
              {templateBody && (
                <p className="text-xs text-gray-600 line-clamp-3 border-t border-gray-100 pt-2 whitespace-pre-wrap">
                  {templateBody}
                </p>
              )}
            </div>

            <div className="max-h-64 overflow-y-auto rounded-lg border border-border divide-y divide-gray-100">
              {selectedApps.map(a => {
                const d = decisionFor(a.id)
                return (
                  <div key={a.id} className="flex items-center justify-between gap-3 px-3 py-2">
                    <div className="min-w-0">
                      <p className="text-sm font-medium text-gray-900 truncate">{applicantLabel(a)}</p>
                      <p className="text-xs text-gray-500 truncate">{a.program?.program_name ?? 'Program'}</p>
                    </div>
                    <div className="flex items-center gap-2 shrink-0">
                      <Badge variant={DECISION_TONE[d]}>{decisionLabel(d)}</Badge>
                      <Select
                        label=""
                        options={INSTITUTION_DECISIONS.map(o => ({ value: o.value, label: o.label }))}
                        value={d}
                        onChange={e => setPerApp(prev => ({ ...prev, [a.id]: e.target.value as InstitutionDecision }))}
                        className="w-40"
                      />
                    </div>
                  </div>
                )
              })}
            </div>

            {releaseMut.isPending && (
              <div className="space-y-1">
                <div className="h-1.5 w-full overflow-hidden rounded-full bg-muted">
                  <div
                    className="h-full rounded-full bg-cobalt transition-all duration-300"
                    style={{ width: `${releaseProgress}%` }}
                  />
                </div>
                <p className="text-xs text-gray-500">Batch release in progress…</p>
              </div>
            )}

            <div className="flex justify-end gap-2">
              <Button variant="tertiary" onClick={close}>Cancel</Button>
              <Button variant="secondary" onClick={() => setStep('confirm')} disabled={selectedApps.length === 0}>
                Review &amp; confirm · {selectedApps.length}
              </Button>
            </div>
          </>
        )}

        {step === 'confirm' && !result && (
          <>
            <p className="text-sm text-gray-600">
              You are about to release {selectedApps.length} decision{selectedApps.length === 1 ? '' : 's'}. Each release is audit-logged.
            </p>
            {standardOffer && formatOfferTermsSummary(standardOffer).length > 0 && (
              <div className="rounded-lg border border-border p-3 text-sm text-gray-700">
                <p className="text-xs font-medium text-gray-500 mb-1">Shared offer terms (admits)</p>
                <ul className="list-disc list-inside">
                  {formatOfferTermsSummary(standardOffer).map(line => (
                    <li key={line}>{line}</li>
                  ))}
                </ul>
              </div>
            )}
            <ul className="max-h-48 overflow-y-auto text-sm space-y-1">
              {selectedApps.map(a => (
                <li key={a.id} className="flex justify-between gap-2">
                  <span className="truncate">{applicantLabel(a)}</span>
                  <Badge variant={DECISION_TONE[decisionFor(a.id)]}>{decisionLabel(decisionFor(a.id))}</Badge>
                </li>
              ))}
            </ul>
            {releaseMut.isPending && (
              <div className="h-1.5 w-full overflow-hidden rounded-full bg-muted">
                <div
                  className="h-full rounded-full bg-cobalt transition-all duration-300"
                  style={{ width: `${Math.max(releaseProgress, 20)}%` }}
                />
              </div>
            )}
            <div className="flex justify-end gap-2">
              <Button variant="tertiary" onClick={() => setStep('configure')} disabled={releaseMut.isPending}>
                Back
              </Button>
              <Button variant="secondary" onClick={() => releaseMut.mutate()} disabled={releaseMut.isPending}>
                {releaseMut.isPending ? 'Releasing…' : `Confirm release · ${selectedApps.length}`}
              </Button>
            </div>
          </>
        )}

        {result && (
          <div className="flex items-center justify-between rounded-lg bg-success-soft px-3 py-2 text-sm text-success">
            <span>
              Released {result.success_count} decision{result.success_count === 1 ? '' : 's'}
              {result.failed_count ? ` · ${result.failed_count} failed` : ''}.
            </span>
            <Button variant="secondary" size="sm" onClick={close}>Done</Button>
          </div>
        )}
      </div>
    </Modal>
  )
}
