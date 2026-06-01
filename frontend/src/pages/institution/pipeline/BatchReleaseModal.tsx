import { useMemo, useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { batchReleaseDecisionV2 } from '../../../api/applications-admin'
import Modal from '../../../components/ui/Modal'
import Button from '../../../components/ui/Button'
import Select from '../../../components/ui/Select'
import Input from '../../../components/ui/Input'
import Badge from '../../../components/ui/Badge'
import { showToast } from '../../../stores/toast-store'
import type { Application, BatchReleaseItem, InstitutionDecision } from '../../../types'

const DECISION_OPTIONS: { value: InstitutionDecision; label: string }[] = [
  { value: 'admitted', label: 'Admit' },
  { value: 'conditional_admission', label: 'Conditional admit' },
  { value: 'waitlisted', label: 'Waitlist' },
  { value: 'deferred', label: 'Defer' },
  { value: 'rejected', label: 'Reject' },
]

const DECISION_TONE: Record<InstitutionDecision, 'success' | 'info' | 'warning' | 'neutral' | 'danger'> = {
  admitted: 'success',
  conditional_admission: 'info',
  waitlisted: 'warning',
  deferred: 'neutral',
  rejected: 'danger',
}

/** Batch decision release (spec 34 §5): confirm a decision per applicant, apply a
 *  standard offer template to admits, and release with per-applicant audit. */
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
  const [bulk, setBulk] = useState<InstitutionDecision>('admitted')
  const [perApp, setPerApp] = useState<Record<string, InstitutionDecision>>({})
  // Standard offer template applied to every admit / conditional admit.
  const [scholarship, setScholarship] = useState('')
  const [deadline, setDeadline] = useState('')
  const [result, setResult] = useState<{ success_count: number; failed_count: number } | null>(null)

  const decisionFor = (id: string): InstitutionDecision => perApp[id] ?? bulk
  const admitCount = useMemo(
    () => selectedApps.filter(a => ['admitted', 'conditional_admission'].includes(decisionFor(a.id))).length,
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [selectedApps, perApp, bulk],
  )

  const releaseMut = useMutation({
    mutationFn: () => {
      const offer =
        scholarship || deadline
          ? {
              scholarship_amount: scholarship ? Number(scholarship) : null,
              response_deadline: deadline || null,
            }
          : null
      const items: BatchReleaseItem[] = selectedApps.map(a => {
        const decision = decisionFor(a.id)
        const isOffer = decision === 'admitted' || decision === 'conditional_admission'
        return {
          application_id: a.id,
          decision,
          offer: isOffer ? offer : null,
        }
      })
      return batchReleaseDecisionV2(items)
    },
    onSuccess: data => {
      setResult({ success_count: data.success_count, failed_count: data.failed_count })
      showToast(
        `${data.success_count} released` + (data.failed_count ? `, ${data.failed_count} failed` : ''),
        data.failed_count ? 'warning' : 'success',
      )
      onDone()
    },
    onError: () => showToast('Batch release failed', 'error'),
  })

  const close = () => {
    setResult(null)
    setPerApp({})
    onClose()
  }

  return (
    <Modal isOpen={isOpen} onClose={close} title="Release decisions" size="lg">
      <div className="space-y-4">
        {!result && (
          <>
            <div className="flex flex-wrap items-end gap-3">
              <Select
                label="Decision for all"
                options={DECISION_OPTIONS}
                value={bulk}
                onChange={e => setBulk(e.target.value as InstitutionDecision)}
                className="w-48"
              />
              <p className="text-xs text-gray-500 pb-2">
                Set a default, then override individuals below.
              </p>
            </div>

            {/* Standard offer template (applied to admits / conditional admits) */}
            <div className="rounded-lg border border-border p-3 space-y-3">
              <p className="text-xs font-medium text-gray-500">
                Standard offer template — applied to {admitCount} admit{admitCount === 1 ? '' : 's'}
              </p>
              <div className="grid grid-cols-2 gap-3">
                <Input label="Scholarship ($)" type="number" value={scholarship} onChange={e => setScholarship(e.target.value)} />
                <Input label="Response deadline" type="date" value={deadline} onChange={e => setDeadline(e.target.value)} />
              </div>
            </div>

            {/* Per-applicant confirmation list */}
            <div className="max-h-64 overflow-y-auto rounded-lg border border-border divide-y divide-gray-100">
              {selectedApps.map(a => {
                const d = decisionFor(a.id)
                return (
                  <div key={a.id} className="flex items-center justify-between gap-3 px-3 py-2">
                    <div className="min-w-0">
                      <p className="text-sm font-medium text-gray-900 truncate">
                        Applicant {a.student_id.slice(0, 8)}
                      </p>
                      <p className="text-xs text-gray-500 truncate">{a.program?.program_name ?? 'Program'}</p>
                    </div>
                    <div className="flex items-center gap-2 shrink-0">
                      <Badge variant={DECISION_TONE[d]}>{DECISION_OPTIONS.find(o => o.value === d)?.label}</Badge>
                      <Select
                        label=""
                        options={DECISION_OPTIONS}
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
                <div className="h-full w-1/2 animate-pulse rounded-full bg-cobalt" />
              </div>
            )}
          </>
        )}

        {result ? (
          <div className="flex items-center justify-between rounded-lg bg-success-soft px-3 py-2 text-sm text-success">
            <span>
              Released {result.success_count} decision{result.success_count === 1 ? '' : 's'}
              {result.failed_count ? ` · ${result.failed_count} failed` : ''}.
            </span>
            <Button variant="secondary" size="sm" onClick={close}>Done</Button>
          </div>
        ) : (
          <div className="flex justify-end gap-2">
            <Button variant="tertiary" onClick={close}>Cancel</Button>
            <Button variant="secondary" onClick={() => releaseMut.mutate()} disabled={releaseMut.isPending}>
              {releaseMut.isPending ? 'Releasing…' : `Confirm release · ${selectedApps.length}`}
            </Button>
          </div>
        )}
      </div>
    </Modal>
  )
}
