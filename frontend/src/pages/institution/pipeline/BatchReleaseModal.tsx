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

/** Batch decision release (spec 34 §5). */
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
  const [offerTemplateId, setOfferTemplateId] = useState('')
  const [offerTemplateBody, setOfferTemplateBody] = useState('')
  const [decisionTemplateId, setDecisionTemplateId] = useState('')
  const [decisionTemplateBody, setDecisionTemplateBody] = useState('')
  const [releaseProgress, setReleaseProgress] = useState(0)
  const [result, setResult] = useState<{ success_count: number; failed_count: number } | null>(null)

  const offerTemplatesQ = useQuery({
    queryKey: ['templates', 'offer_notice'],
    queryFn: () => getTemplates('offer_notice'),
    enabled: isOpen,
  })
  const decisionTemplatesQ = useQuery({
    queryKey: ['templates', 'decision_notice'],
    queryFn: () => getTemplates('decision_notice'),
    enabled: isOpen,
  })
  const offerTemplates = offerTemplatesQ.data ?? []
  const decisionTemplates = decisionTemplatesQ.data ?? []

  const alreadyReleased = useMemo(() => selectedApps.filter(a => a.decision), [selectedApps])
  const notInDecisionStage = useMemo(
    () => selectedApps.filter(a => a.status !== 'decision_made'),
    [selectedApps],
  )

  useEffect(() => {
    if (!isOpen) {
      setStep('configure')
      setPerApp({})
      setResult(null)
      setReleaseProgress(0)
      setOfferTemplateId('')
      setOfferTemplateBody('')
      setDecisionTemplateId('')
      setDecisionTemplateBody('')
    }
  }, [isOpen])

  const previewFor = (templateId: string, setter: (body: string) => void) => {
    if (!templateId || selectedApps.length === 0) {
      setter('')
      return () => {}
    }
    let cancelled = false
    previewTemplate(templateId, selectedApps[0].id)
      .then(p => { if (!cancelled) setter(p.rendered_body) })
      .catch(() => { if (!cancelled) setter('') })
    return () => { cancelled = true }
  }

  useEffect(() => previewFor(offerTemplateId, setOfferTemplateBody), [offerTemplateId, selectedApps])
  useEffect(() => previewFor(decisionTemplateId, setDecisionTemplateBody), [decisionTemplateId, selectedApps])

  const decisionFor = (id: string): InstitutionDecision => perApp[id] ?? bulk
  const admitCount = useMemo(
    () => selectedApps.filter(a => isOfferDecision(decisionFor(a.id))).length,
    [selectedApps, perApp, bulk],
  )
  const nonOfferCount = selectedApps.length - admitCount

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
        const d = decisionFor(a.id)
        const isOffer = isOfferDecision(d)
        return {
          application_id: a.id,
          decision: d,
          offer: isOffer ? offer : null,
          message: isOffer
            ? (offerTemplateBody.trim() || null)
            : (decisionTemplateBody.trim() || null),
        }
      })
      setReleaseProgress(20)
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
    },
    onError: () => {
      setReleaseProgress(0)
      showToast('Batch release failed', 'error')
    },
  })

  const close = () => {
    const hadResult = !!result
    setResult(null)
    setPerApp({})
    setStep('configure')
    onClose()
    if (hadResult) onDone()
  }

  return (
    <Modal isOpen={isOpen} onClose={close} title="Release decisions" size="lg">
      <div className="space-y-4">
        {step === 'configure' && !result && (
          <>
            <p className="text-sm text-muted-foreground">
              Confirm a decision for each applicant. Offer terms apply to admits and conditional admits.
            </p>
            {notInDecisionStage.length > 0 && (
              <p className="text-xs text-warning rounded-lg border border-warning/30 bg-warning-soft/30 px-3 py-2">
                {notInDecisionStage.length} selected applicant{notInDecisionStage.length === 1 ? ' is' : 's are'} not in the Decision stage.
              </p>
            )}
            {alreadyReleased.length > 0 && (
              <p className="text-xs text-muted-foreground rounded-lg border border-border bg-muted/50 px-3 py-2">
                {alreadyReleased.length} already have a released decision — confirming will re-release and re-notify.
              </p>
            )}
            <div className="flex flex-wrap items-end gap-3">
              <Select
                label="Decision for all"
                options={INSTITUTION_DECISIONS.map(d => ({ value: d.value, label: d.label }))}
                value={bulk}
                onChange={e => setBulk(e.target.value as InstitutionDecision)}
                className="w-48"
              />
            </div>

            {admitCount > 0 && (
              <div className="rounded-lg border border-border p-3 space-y-3">
                <p className="text-xs font-medium text-muted-foreground">Standard offer — {admitCount} admit{admitCount === 1 ? '' : 's'}</p>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <Input label="Scholarship ($)" type="number" min={0} value={scholarship} onChange={e => setScholarship(e.target.value)} />
                  <Input label="Response deadline" type="date" value={deadline} onChange={e => setDeadline(e.target.value)} />
                </div>
                <Select
                  label="Offer letter template"
                  options={[{ value: '', label: 'Standard offer notice' }, ...offerTemplates.map(t => ({ value: t.id, label: t.name }))]}
                  value={offerTemplateId}
                  onChange={e => setOfferTemplateId(e.target.value)}
                />
                {offerTemplateBody && <p className="text-xs text-muted-foreground line-clamp-3 whitespace-pre-wrap">{offerTemplateBody}</p>}
              </div>
            )}

            {nonOfferCount > 0 && (
              <div className="rounded-lg border border-border p-3 space-y-2">
                <p className="text-xs font-medium text-muted-foreground">Decision notice — {nonOfferCount} non-admit{nonOfferCount === 1 ? '' : 's'}</p>
                <Select
                  label="Decision notice template"
                  options={[{ value: '', label: 'Standard decision notice' }, ...decisionTemplates.map(t => ({ value: t.id, label: t.name }))]}
                  value={decisionTemplateId}
                  onChange={e => setDecisionTemplateId(e.target.value)}
                />
                {decisionTemplateBody && <p className="text-xs text-muted-foreground line-clamp-3 whitespace-pre-wrap">{decisionTemplateBody}</p>}
              </div>
            )}

            <div className="max-h-64 overflow-y-auto rounded-lg border border-border divide-y divide-border">
              {selectedApps.map(a => {
                const d = decisionFor(a.id)
                return (
                  <div key={a.id} className="flex items-center justify-between gap-3 px-3 py-2">
                    <div className="min-w-0">
                      <p className="text-sm font-medium text-foreground truncate">{applicantLabel(a)}</p>
                      <p className="text-xs text-muted-foreground truncate">{a.program?.program_name ?? 'Program'}</p>
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
              <div className="h-1.5 w-full overflow-hidden rounded-full bg-muted">
                <div className="h-full rounded-full bg-secondary transition-all duration-300" style={{ width: `${releaseProgress}%` }} />
              </div>
            )}

            <div className="flex justify-end gap-2">
              <Button variant="tertiary" onClick={close}>Cancel</Button>
              <Button variant="secondary" onClick={() => setStep('confirm')} disabled={!selectedApps.length}>
                Review &amp; confirm · {selectedApps.length}
              </Button>
            </div>
          </>
        )}

        {step === 'confirm' && !result && (
          <>
            <p className="text-sm text-muted-foreground">
              Release {selectedApps.length} decision{selectedApps.length === 1 ? '' : 's'}? Each is audit-logged.
            </p>
            {standardOffer && formatOfferTermsSummary(standardOffer).length > 0 && (
              <ul className="text-sm list-disc list-inside text-foreground">
                {formatOfferTermsSummary(standardOffer).map(line => (
                  <li key={line}>{line}</li>
                ))}
              </ul>
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
                <div className="h-full rounded-full bg-secondary transition-all duration-300" style={{ width: `${Math.max(releaseProgress, 20)}%` }} />
              </div>
            )}
            <div className="flex justify-end gap-2">
              <Button variant="tertiary" onClick={() => setStep('configure')} disabled={releaseMut.isPending}>Back</Button>
              <Button variant="secondary" onClick={() => releaseMut.mutate()} disabled={releaseMut.isPending}>
                {releaseMut.isPending ? 'Releasing…' : `Confirm release · ${selectedApps.length}`}
              </Button>
            </div>
          </>
        )}

        {result && (
          <div className="flex items-center justify-between rounded-lg bg-success-soft px-3 py-2 text-sm text-success">
            <span>
              Released {result.success_count}
              {result.failed_count ? ` · ${result.failed_count} failed` : ''}.
            </span>
            <Button variant="secondary" size="sm" onClick={close}>Done</Button>
          </div>
        )}
      </div>
    </Modal>
  )
}
