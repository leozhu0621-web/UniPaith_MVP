import { useEffect, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  AlertTriangle,
  Check,
  Download,
  FileText,
  Globe,
  GraduationCap,
  Languages,
  Lock,
  Plane,
  Sparkles,
} from 'lucide-react'
import {
  generateImmigrationDoc,
  getInternational,
  normalizeGpa,
  suggestCountryPack,
  updateInternational,
  type IntlPatch,
} from '../../../api/international'
import type { IntlCountryRequirement, IntlFeasibilityBand } from '../../../types'
import Card from '../../../components/ui/Card'
import Badge from '../../../components/ui/Badge'
import Button from '../../../components/ui/Button'
import Input from '../../../components/ui/Input'
import Select from '../../../components/ui/Select'
import Textarea from '../../../components/ui/Textarea'
import Skeleton from '../../../components/ui/Skeleton'
import QueryError from '../../../components/ui/QueryError'
import AIBadge from '../../../components/ui/AIBadge'
import FallbackNote from '../../../components/ui/FallbackNote'
import { Toggle } from '../program-editor/widgets'
import { showToast } from '../../../stores/toast-store'

const FEASIBILITY_BADGE: Record<IntlFeasibilityBand, 'success' | 'info' | 'warning' | 'danger'> = {
  strong: 'success',
  moderate: 'info',
  at_risk: 'warning',
  blocked: 'danger',
}
const FEASIBILITY_LABEL: Record<IntlFeasibilityBand, string> = {
  strong: 'Strong',
  moderate: 'Moderate',
  at_risk: 'At risk',
  blocked: 'Blocked',
}
const REQ_STATUS_OPTIONS = [
  { value: 'pending', label: 'Pending' },
  { value: 'received', label: 'Received' },
  { value: 'verified', label: 'Verified' },
  { value: 'waived', label: 'Waived' },
]
const PROVIDER_OPTIONS = [
  { value: '', label: '—' },
  { value: 'WES', label: 'WES' },
  { value: 'ECE', label: 'ECE' },
  { value: 'SpanTran', label: 'SpanTran' },
  { value: 'other', label: 'Other' },
]
const CRED_STATUS_OPTIONS = [
  { value: 'none', label: 'Not started' },
  { value: 'requested', label: 'Requested' },
  { value: 'in_progress', label: 'In progress' },
  { value: 'received', label: 'Received' },
  { value: 'verified', label: 'Verified' },
]
const ENGLISH_TEST_OPTIONS = [
  { value: '', label: '—' },
  { value: 'TOEFL', label: 'TOEFL' },
  { value: 'IELTS', label: 'IELTS' },
  { value: 'DET', label: 'Duolingo (DET)' },
  { value: 'PTE', label: 'PTE' },
]
const VISA_OUTCOME_OPTIONS = [
  { value: '', label: 'Not scheduled' },
  { value: 'pending', label: 'Pending' },
  { value: 'approved', label: 'Approved' },
  { value: 'denied', label: 'Denied' },
]

interface Draft {
  credential_provider: string
  credential_status: string
  credential_report_ref: string
  credential_notes: string
  english_test: string
  english_score: string
  english_meets_minimum: boolean | null
  english_waiver_eligible: boolean
  english_waiver_basis: string
  country_requirements: IntlCountryRequirement[]
  visa_appointment_at: string
  visa_consulate: string
  visa_outcome: string
}

function SectionTitle({ icon, children }: { icon: React.ReactNode; children: React.ReactNode }) {
  return (
    <div className="flex items-center gap-2 mb-4">
      <span className="text-secondary">{icon}</span>
      <h3 className="text-sm font-semibold text-foreground">{children}</h3>
    </div>
  )
}

export default function InternationalTab({ applicationId }: { applicationId: string }) {
  const qc = useQueryClient()
  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['international', applicationId],
    queryFn: () => getInternational(applicationId),
  })

  const [draft, setDraft] = useState<Draft | null>(null)
  const [normNote, setNormNote] = useState<{ ai: boolean; text: string | null } | null>(null)
  const [docType, setDocType] = useState<'I-20' | 'DS-2019'>('I-20')

  useEffect(() => {
    if (!data?.processing) {
      setDraft(d => d ?? blankDraft())
      return
    }
    const p = data.processing
    setDraft({
      credential_provider: p.credential_eval.provider ?? '',
      credential_status: p.credential_eval.status ?? 'none',
      credential_report_ref: p.credential_eval.report_ref ?? '',
      credential_notes: p.credential_eval.notes ?? '',
      english_test: p.english_proficiency.test ?? '',
      english_score: p.english_proficiency.score ?? '',
      english_meets_minimum: p.english_proficiency.meets_minimum,
      english_waiver_eligible: p.english_proficiency.waiver.eligible,
      english_waiver_basis: p.english_proficiency.waiver.basis ?? '',
      country_requirements: p.country_requirements ?? [],
      visa_appointment_at: p.visa.appointment_at ? p.visa.appointment_at.slice(0, 10) : '',
      visa_consulate: p.visa.consulate ?? '',
      visa_outcome: p.visa.outcome ?? '',
    })
  }, [data?.processing?.id, data?.processing])

  const invalidate = () => qc.invalidateQueries({ queryKey: ['international', applicationId] })

  const saveMut = useMutation({
    mutationFn: (patch: IntlPatch) => updateInternational(applicationId, patch),
    onSuccess: () => {
      showToast('International processing saved', 'success')
      invalidate()
    },
    onError: () => showToast('Failed to save', 'error'),
  })

  const normalizeMut = useMutation({
    mutationFn: () => normalizeGpa(applicationId),
    onSuccess: res => {
      setNormNote({ ai: res.ai_used, text: res.course_map_note })
      showToast(`Normalized GPA: ${res.normalized_gpa} (from ${res.source_scale})`, 'success')
      invalidate()
    },
    onError: () => showToast('Could not normalize — enter the GPA manually', 'error'),
  })

  const suggestMut = useMutation({
    mutationFn: () => suggestCountryPack(applicationId),
    onSuccess: res => {
      setDraft(d => (d ? { ...d, country_requirements: res.requirements } : d))
      showToast(`Attached ${res.requirements.length} requirement(s) for ${res.country_name}`, 'success')
    },
    onError: () => showToast('Could not suggest a pack', 'error'),
  })

  const generateMut = useMutation({
    mutationFn: () => generateImmigrationDoc(applicationId, docType),
    onSuccess: res => {
      showToast(`${res.doc_type} drafted (SEVIS ${res.sevis_id})`, 'success')
      invalidate()
    },
    onError: (e: unknown) => {
      const detail = (e as { response?: { data?: { detail?: { message?: string } } } })?.response?.data
        ?.detail
      showToast(detail?.message ?? 'Could not generate document', 'error')
    },
  })

  if (isError && !data) {
    return (
      <Card pad={false} className="p-2">
        <QueryError detail="We couldn't load this applicant's international processing." onRetry={() => refetch()} />
      </Card>
    )
  }
  if (isLoading || !data || !draft) return <Skeleton className="h-96" />

  if (!data.is_international) {
    return (
      <Card pad={false} className="p-6 text-center">
        <Globe size={28} className="mx-auto mb-3 text-muted-foreground" />
        <p className="text-sm text-muted-foreground">This applicant is domestic.</p>
      </Card>
    )
  }

  const si = data.student_inputs
  const rec = data.processing
  const gate = data.immigration_gate
  const feas = data.feasibility
  const waiverSuggestion = data.english_waiver_suggestion

  const save = () => {
    const patch: IntlPatch = {
      credential_status: draft.credential_status as IntlPatch['credential_status'],
      credential_report_ref: draft.credential_report_ref || undefined,
      credential_notes: draft.credential_notes || undefined,
      english_meets_minimum: draft.english_meets_minimum ?? undefined,
      english_waiver_eligible: draft.english_waiver_eligible,
      english_waiver_basis: draft.english_waiver_basis || undefined,
      country_requirements: draft.country_requirements,
      visa_consulate: draft.visa_consulate || undefined,
    }
    if (draft.credential_provider) patch.credential_provider = draft.credential_provider as IntlPatch['credential_provider']
    if (draft.english_test) patch.english_test = draft.english_test as IntlPatch['english_test']
    if (draft.english_score) patch.english_score = Number(draft.english_score)
    if (draft.visa_appointment_at) patch.visa_appointment_at = new Date(draft.visa_appointment_at).toISOString()
    if (draft.visa_outcome) patch.visa_outcome = draft.visa_outcome as IntlPatch['visa_outcome']
    saveMut.mutate(patch)
  }

  const downloadSevis = () => {
    if (!rec?.immigration_doc.sevis_export) return
    const blob = new Blob([JSON.stringify(rec.immigration_doc.sevis_export, null, 2)], {
      type: 'application/json',
    })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `sevis-${rec.immigration_doc.type}-${applicationId.slice(0, 8)}.json`
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="space-y-4">
      {/* Feasibility + fairness contract banner (§3) */}
      <div className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-border bg-muted/40 px-4 py-3">
        <div className="flex items-center gap-2">
          <span className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
            Visa feasibility
          </span>
          <Badge variant={FEASIBILITY_BADGE[feas.band]}>{FEASIBILITY_LABEL[feas.band]}</Badge>
          {feas.reasons[0] && (
            <span className="text-xs text-muted-foreground">· {feas.reasons.join(' · ')}</span>
          )}
        </div>
        <p className="text-[11px] italic text-muted-foreground max-w-md">
          Operational only — visa &amp; immigration status inform feasibility and yield planning, never
          a selection criterion.
        </p>
      </div>

      {/* Credential evaluation (§2.1) */}
      <Card pad={false} className="p-5">
        <SectionTitle icon={<GraduationCap size={16} />}>Credential evaluation</SectionTitle>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <Select
            label="Evaluation provider"
            options={PROVIDER_OPTIONS}
            value={draft.credential_provider}
            onChange={e => setDraft({ ...draft, credential_provider: e.target.value })}
          />
          <Select
            label="Status"
            options={CRED_STATUS_OPTIONS}
            value={draft.credential_status}
            onChange={e => setDraft({ ...draft, credential_status: e.target.value })}
          />
        </div>
        <div className="mt-4 rounded-lg border border-border bg-muted/30 p-4">
          <div className="flex flex-wrap items-baseline justify-between gap-2">
            <div className="text-sm text-foreground">
              <span className="text-muted-foreground">Raw GPA: </span>
              <span className="font-semibold tabular-nums">{si.raw_gpa ?? '—'}</span>
              {si.gpa_scale && <span className="text-muted-foreground"> ({si.gpa_scale})</span>}
            </div>
            <div className="text-sm text-foreground">
              <span className="text-muted-foreground">Normalized GPA: </span>
              <span className="font-semibold tabular-nums text-secondary">
                {rec?.credential_eval.normalized_gpa ?? '—'}
              </span>
              {rec?.credential_eval.source_scale && (
                <span className="text-muted-foreground"> (from {rec.credential_eval.source_scale})</span>
              )}
            </div>
          </div>
          <div className="mt-3 flex flex-wrap items-center gap-3">
            <Button
              variant="secondary"
              size="sm"
              loading={normalizeMut.isPending}
              onClick={() => normalizeMut.mutate()}
              className="gap-1.5"
            >
              <Sparkles size={14} /> Normalize GPA
            </Button>
            {normNote && (normNote.ai ? <AIBadge /> : <AIBadge fallback />)}
          </div>
          {normNote?.text && <p className="mt-2 text-xs text-muted-foreground">{normNote.text}</p>}
          {normNote && !normNote.ai && <FallbackNote className="mt-1" />}
        </div>
        <div className="mt-4">
          <Input
            label="Evaluation report reference"
            value={draft.credential_report_ref}
            onChange={e => setDraft({ ...draft, credential_report_ref: e.target.value })}
            placeholder="WES reference # or document link"
          />
          {si.credential_report_url && (
            <p className="mt-1 text-xs text-muted-foreground">
              Student uploaded:{' '}
              <a className="text-secondary hover:underline" href={si.credential_report_url} target="_blank" rel="noreferrer">
                view report
              </a>
            </p>
          )}
        </div>
        <div className="mt-4">
          <Textarea
            label="Reviewer notes"
            value={draft.credential_notes}
            onChange={e => setDraft({ ...draft, credential_notes: e.target.value })}
            rows={2}
            placeholder="Grading-system context, caveats…"
          />
        </div>
      </Card>

      {/* English proficiency (§2.2) */}
      <Card pad={false} className="p-5">
        <SectionTitle icon={<Languages size={16} />}>English proficiency</SectionTitle>
        {waiverSuggestion.eligible && !draft.english_waiver_eligible && (
          <div className="mb-4 flex flex-wrap items-center justify-between gap-2 rounded-lg border border-secondary/30 bg-secondary/5 px-3 py-2">
            <span className="text-sm text-secondary">
              Waiver eligible — {waiverSuggestion.basis}. Confirm to apply.
            </span>
            <Button
              variant="secondary"
              size="sm"
              onClick={() =>
                setDraft({
                  ...draft,
                  english_waiver_eligible: true,
                  english_waiver_basis: waiverSuggestion.basis ?? '',
                })
              }
            >
              Apply waiver
            </Button>
          </div>
        )}
        {si.english_test_scores.length > 0 && (
          <div className="mb-4 flex flex-wrap gap-1.5">
            {si.english_test_scores.map((t, i) => (
              <span key={i} className="rounded bg-muted px-2 py-0.5 text-xs text-muted-foreground">
                {t.test}: {t.score ?? '—'}
              </span>
            ))}
          </div>
        )}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <Select
            label="Test"
            options={ENGLISH_TEST_OPTIONS}
            value={draft.english_test}
            onChange={e => setDraft({ ...draft, english_test: e.target.value })}
          />
          <Input
            label="Verified score"
            type="number"
            min={0}
            value={draft.english_score}
            onChange={e => setDraft({ ...draft, english_score: e.target.value })}
            placeholder="e.g. 100"
          />
        </div>
        <div className="mt-4 flex flex-col gap-3">
          <Toggle
            checked={draft.english_meets_minimum === true}
            onChange={v => setDraft({ ...draft, english_meets_minimum: v })}
            label="Meets the program's minimum score"
          />
          <Toggle
            checked={draft.english_waiver_eligible}
            onChange={v => setDraft({ ...draft, english_waiver_eligible: v })}
            label="Waiver eligible"
          />
          {draft.english_waiver_eligible && (
            <Input
              label="Waiver basis"
              value={draft.english_waiver_basis}
              onChange={e => setDraft({ ...draft, english_waiver_basis: e.target.value })}
              placeholder="e.g. Prior degree completed in English"
            />
          )}
        </div>
      </Card>

      {/* Country requirements (§2.3) */}
      <Card pad={false} className="p-5">
        <div className="flex items-center justify-between gap-2 mb-4">
          <SectionTitle icon={<FileText size={16} />}>Country-specific requirements</SectionTitle>
          <div className="flex items-center gap-2">
            {suggestMut.data?.ai_used && <AIBadge />}
            <Button
              variant="secondary"
              size="sm"
              loading={suggestMut.isPending}
              onClick={() => suggestMut.mutate()}
              className="gap-1.5"
            >
              <Sparkles size={14} /> Suggest pack
            </Button>
          </div>
        </div>
        {si.nationality && (
          <p className="-mt-2 mb-3 text-xs text-muted-foreground">
            Based on nationality: <span className="font-medium text-foreground">{si.nationality}</span>
          </p>
        )}
        <div className="space-y-2">
          {draft.country_requirements.length === 0 && (
            <p className="text-sm italic text-muted-foreground">No country requirements yet.</p>
          )}
          {draft.country_requirements.map((req, i) => (
            <div key={i} className="flex items-center gap-2">
              <Input
                value={req.item}
                onChange={e => {
                  const next = [...draft.country_requirements]
                  next[i] = { ...next[i], item: e.target.value }
                  setDraft({ ...draft, country_requirements: next })
                }}
                className="flex-1"
              />
              <div className="w-40 shrink-0">
                <Select
                  options={REQ_STATUS_OPTIONS}
                  value={req.status}
                  onChange={e => {
                    const next = [...draft.country_requirements]
                    next[i] = { ...next[i], status: e.target.value as IntlCountryRequirement['status'] }
                    setDraft({ ...draft, country_requirements: next })
                  }}
                />
              </div>
              <button
                type="button"
                onClick={() =>
                  setDraft({
                    ...draft,
                    country_requirements: draft.country_requirements.filter((_, x) => x !== i),
                  })
                }
                className="shrink-0 rounded-md p-2 text-muted-foreground hover:text-error hover:bg-error-soft/60"
                aria-label="Remove requirement"
              >
                ×
              </button>
            </div>
          ))}
          <Button
            variant="ghost"
            size="sm"
            onClick={() =>
              setDraft({
                ...draft,
                country_requirements: [...draft.country_requirements, { item: '', status: 'pending' }],
              })
            }
          >
            + Add requirement
          </Button>
        </div>
      </Card>

      {/* Immigration document — HIGH SENSITIVITY (§2.4 / §7 / 46) */}
      <Card pad={false} className="p-5 border-warning/40">
        <div className="flex items-center gap-2 mb-1">
          <Lock size={15} className="text-warning" />
          <h3 className="text-sm font-semibold text-foreground">Immigration document</h3>
          <Badge variant="warning">High sensitivity</Badge>
        </div>
        <p className="mb-4 text-xs text-muted-foreground">
          Access-gated &amp; audit-logged. You upload the export to SEVIS yourself.
        </p>

        <div className="mb-3 flex flex-wrap items-center gap-3 text-sm">
          <span className="text-muted-foreground">Financial proof:</span>
          {si.financial_proof_available ? (
            <Badge variant="success">
              <Check size={12} /> On file{si.financial_proof_amount_band ? ` (${si.financial_proof_amount_band})` : ''}
            </Badge>
          ) : (
            <Badge variant="danger">Not on file</Badge>
          )}
        </div>

        {rec && rec.immigration_doc.status !== 'not_started' ? (
          <div className="rounded-lg border border-border bg-muted/30 p-4">
            <div className="flex flex-wrap items-center gap-2">
              <Badge variant="info">{rec.immigration_doc.type}</Badge>
              <Badge variant="neutral">{rec.immigration_doc.status}</Badge>
              {rec.immigration_doc.sevis_id && (
                <span className="text-xs text-muted-foreground">SEVIS {rec.immigration_doc.sevis_id}</span>
              )}
              {rec.immigration_doc.issued_at && (
                <span className="text-xs text-muted-foreground">
                  · {new Date(rec.immigration_doc.issued_at).toLocaleDateString()}
                </span>
              )}
            </div>
            <Button variant="tertiary" size="sm" onClick={downloadSevis} className="mt-3 gap-1.5">
              <Download size={14} /> Download SEVIS export
            </Button>
          </div>
        ) : gate.can_generate ? (
          <div className="flex flex-wrap items-end gap-3">
            <div className="w-44">
              <Select
                label="Document type"
                options={[
                  { value: 'I-20', label: 'I-20 (F-1)' },
                  { value: 'DS-2019', label: 'DS-2019 (J-1)' },
                ]}
                value={docType}
                onChange={e => setDocType(e.target.value as 'I-20' | 'DS-2019')}
              />
            </div>
            <Button
              variant="secondary"
              loading={generateMut.isPending}
              onClick={() => generateMut.mutate()}
            >
              Generate {docType}
            </Button>
          </div>
        ) : (
          <div className="rounded-lg border border-warning/40 bg-warning-soft px-4 py-3">
            <div className="flex items-center gap-2 text-sm font-medium text-warning">
              <AlertTriangle size={15} /> Not ready to issue
            </div>
            <ul className="mt-1.5 space-y-1 text-xs text-warning">
              {gate.blockers.map((b, i) => (
                <li key={i}>• {b.message}</li>
              ))}
              {!data.processing?.immigration_doc && (
                <li>• Applicant must confirm enrollment intent before issuing.</li>
              )}
            </ul>
          </div>
        )}
      </Card>

      {/* Visa interview (§2.5) */}
      <Card pad={false} className="p-5">
        <SectionTitle icon={<Plane size={16} />}>Visa interview</SectionTitle>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <Input
            label="Appointment date"
            type="date"
            value={draft.visa_appointment_at}
            onChange={e => setDraft({ ...draft, visa_appointment_at: e.target.value })}
          />
          <Input
            label="Consulate"
            value={draft.visa_consulate}
            onChange={e => setDraft({ ...draft, visa_consulate: e.target.value })}
            placeholder="e.g. US Consulate Shanghai"
          />
          <Select
            label="Outcome"
            options={VISA_OUTCOME_OPTIONS}
            value={draft.visa_outcome}
            onChange={e => setDraft({ ...draft, visa_outcome: e.target.value })}
          />
        </div>
        {draft.visa_outcome === 'denied' && (
          <div className="mt-3 flex items-center gap-2 rounded-lg border border-warning/40 bg-warning-soft px-3 py-2 text-sm text-warning">
            <AlertTriangle size={15} /> Visa denied — consider an offer deferral from the Enrollment tab.
          </div>
        )}
      </Card>

      {/* Save */}
      <div className="flex justify-end">
        <Button variant="secondary" loading={saveMut.isPending} onClick={save}>
          Save changes
        </Button>
      </div>
    </div>
  )
}

function blankDraft(): Draft {
  return {
    credential_provider: '',
    credential_status: 'none',
    credential_report_ref: '',
    credential_notes: '',
    english_test: '',
    english_score: '',
    english_meets_minimum: null,
    english_waiver_eligible: false,
    english_waiver_basis: '',
    country_requirements: [],
    visa_appointment_at: '',
    visa_consulate: '',
    visa_outcome: '',
  }
}
