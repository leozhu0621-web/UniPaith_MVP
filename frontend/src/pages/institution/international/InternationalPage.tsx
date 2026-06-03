import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { Globe, ChevronDown, Check, X } from 'lucide-react'
import { listCountryRequirements, listInternationalApplicants } from '../../../api/international'
import type { IntlApplicantRow, IntlFeasibilityBand } from '../../../types'
import Card from '../../../components/ui/Card'
import Badge from '../../../components/ui/Badge'
import Table from '../../../components/ui/Table'
import InstitutionPageHeader from '../../../components/institution/InstitutionPageHeader'
import { applicantUrl } from '../../../utils/institution-routes'

const FEASIBILITY_BADGE: Record<IntlFeasibilityBand, 'success' | 'info' | 'warning' | 'danger'> = {
  strong: 'success',
  moderate: 'info',
  at_risk: 'warning',
  blocked: 'danger',
}
const CRED_BADGE: Record<string, 'success' | 'info' | 'warning' | 'neutral'> = {
  verified: 'success',
  received: 'info',
  in_progress: 'warning',
  requested: 'warning',
  none: 'neutral',
}
const DOC_BADGE: Record<string, 'success' | 'info' | 'neutral'> = {
  issued: 'success',
  sent: 'success',
  received: 'success',
  drafted: 'info',
  not_started: 'neutral',
}

function titleCase(s: string | null | undefined) {
  return (s ?? '').replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()) || '—'
}

export default function InternationalPage({ embedded = false }: { embedded?: boolean }) {
  const navigate = useNavigate()
  const [showPacks, setShowPacks] = useState(false)

  const { data: rows = [], isLoading } = useQuery({
    queryKey: ['international-applicants'],
    queryFn: listInternationalApplicants,
  })
  const { data: packs = [] } = useQuery({
    queryKey: ['country-requirement-packs'],
    queryFn: listCountryRequirements,
    enabled: showPacks,
  })

  const columns = [
    { key: 'student_name', label: 'Applicant' },
    { key: 'program_name', label: 'Program', render: (r: IntlApplicantRow) => r.program_name ?? '—' },
    { key: 'nationality', label: 'Country', render: (r: IntlApplicantRow) => r.nationality ?? '—' },
    {
      key: 'credential_status',
      label: 'Credential eval',
      render: (r: IntlApplicantRow) => (
        <Badge variant={CRED_BADGE[r.credential_status] ?? 'neutral'}>
          {titleCase(r.credential_status)}
        </Badge>
      ),
    },
    {
      key: 'normalized_gpa',
      label: 'Norm. GPA',
      numeric: true,
      render: (r: IntlApplicantRow) => r.normalized_gpa ?? '—',
    },
    {
      key: 'english_meets_minimum',
      label: 'English',
      render: (r: IntlApplicantRow) =>
        r.english_meets_minimum == null ? (
          <span className="text-muted-foreground">—</span>
        ) : r.english_meets_minimum ? (
          <Check size={16} className="text-success" />
        ) : (
          <X size={16} className="text-error" />
        ),
    },
    {
      key: 'country_requirements',
      label: 'Docs',
      render: (r: IntlApplicantRow) => (
        <span className="tabular-nums text-muted-foreground">
          {r.country_requirements.complete}/{r.country_requirements.total}
        </span>
      ),
    },
    {
      key: 'immigration_doc_status',
      label: 'I-20 / DS-2019',
      render: (r: IntlApplicantRow) => (
        <Badge variant={DOC_BADGE[r.immigration_doc_status] ?? 'neutral'}>
          {titleCase(r.immigration_doc_status)}
        </Badge>
      ),
    },
    {
      key: 'feasibility',
      label: 'Feasibility',
      render: (r: IntlApplicantRow) => (
        <Badge variant={FEASIBILITY_BADGE[r.feasibility]}>{titleCase(r.feasibility)}</Badge>
      ),
    },
  ]

  return (
    <div className="space-y-4">
      {!embedded && (
        <InstitutionPageHeader
          title="International admissions"
          description="Credential evaluation, English proficiency, country requirements, and immigration documents."
        />
      )}

      <div className="flex items-start gap-2 rounded-lg border border-border bg-muted/40 px-4 py-2.5">
        <Globe size={16} className="mt-0.5 shrink-0 text-secondary" />
        <p className="text-xs text-muted-foreground">
          Visa &amp; immigration status is operational only — it informs feasibility and yield planning
          and is never a selection criterion.
        </p>
      </div>

      <Table
        columns={columns}
        data={rows}
        pageSize={25}
        density="compact"
        isLoading={isLoading}
        onRowClick={(r: IntlApplicantRow) => navigate(applicantUrl(r.application_id, 'international'))}
        emptyMessage="No international applicants in the pipeline yet."
      />

      {/* Country-requirement packs reference (§2.3) */}
      <Card className="p-0 overflow-hidden">
        <button
          type="button"
          onClick={() => setShowPacks(v => !v)}
          className="flex w-full items-center justify-between px-5 py-4 text-left"
          aria-expanded={showPacks}
        >
          <span className="text-sm font-semibold text-foreground">Country-requirement packs</span>
          <ChevronDown
            size={18}
            className={`text-muted-foreground transition-transform ${showPacks ? 'rotate-180' : ''}`}
          />
        </button>
        {showPacks && (
          <div className="border-t border-border px-5 py-4 space-y-4">
            <p className="text-xs text-muted-foreground">
              Platform defaults auto-attach to an applicant's checklist by nationality. Edit per program
              in the program editor's English-proficiency policy, or refine per applicant.
            </p>
            {packs.map(pack => (
              <div key={pack.country_code} className="rounded-lg border border-border p-3">
                <div className="mb-2 flex items-center gap-2">
                  <span className="text-sm font-semibold text-foreground">{pack.country_name}</span>
                  <Badge variant="neutral">{pack.country_code}</Badge>
                  {pack.source === 'institution' && <Badge variant="info">Custom</Badge>}
                </div>
                <ul className="space-y-1">
                  {pack.requirements.map((req, i) => (
                    <li key={i} className="text-xs text-muted-foreground">
                      • {req.item}
                      {req.description ? ` — ${req.description}` : ''}
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  )
}
