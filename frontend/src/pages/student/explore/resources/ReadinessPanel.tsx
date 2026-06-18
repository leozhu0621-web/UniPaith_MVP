// Resources › International — personalized "Your readiness" panel (Spec
// 2026-06-14). Reads ONLY real profile fields (getVisaInfo + listTestScores).
// A present field renders a ✓ row; a missing one renders an "Add in Profile"
// prompt — never a guessed value.
import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { Check, CircleDashed, ListChecks } from 'lucide-react'
import { getVisaInfo, listTestScores } from '../../../../api/students'
import type { StudentVisaInfo } from '../../../../types'

const ENGLISH_TESTS = new Set(['TOEFL', 'IELTS', 'DUOLINGO', 'DET', 'PTE'])

interface ReadinessItem {
  key: string
  label: string
  done: boolean
  value?: string
  to: string
}

export default function ReadinessPanel() {
  const navigate = useNavigate()
  const { data: visa, isLoading: visaLoading } = useQuery<StudentVisaInfo | null>({
    queryKey: ['visa-info'],
    queryFn: getVisaInfo,
    retry: false,
    staleTime: 5 * 60 * 1000,
  })
  const { data: tests } = useQuery<unknown[]>({
    queryKey: ['test-scores'],
    queryFn: listTestScores,
    retry: false,
    staleTime: 5 * 60 * 1000,
  })

  if (visaLoading) return null

  // TestScore uses `test_type` + `total_score` (see AcademicsTab). Find an
  // English test on file and surface its real score — never a guess.
  const englishTest = (Array.isArray(tests) ? tests : []).find(
    (t): t is { test_type: string; total_score: number | null } =>
      typeof t === 'object' &&
      t !== null &&
      ENGLISH_TESTS.has(String((t as { test_type?: unknown }).test_type).toUpperCase()),
  )
  const englishLabel = englishTest
    ? `${englishTest.test_type}${englishTest.total_score != null ? ` ${englishTest.total_score}` : ''} on file`
    : undefined

  // A student who doesn't need a study visa: collapse the checklist (the guide
  // above still applies as general reading).
  if (visa && visa.visa_required === false) {
    return (
      <div className="rounded-xl border border-border bg-card p-5">
        <p className="flex items-center gap-1.5 text-sm font-bold text-foreground">
          <ListChecks size={15} className="text-secondary" aria-hidden /> Your readiness
        </p>
        <p className="mt-1.5 text-[13px] text-muted-foreground">
          You’ve indicated you don’t need a study visa for your target country, so the steps above are
          background reading rather than to-dos.
        </p>
      </div>
    )
  }

  const items: ReadinessItem[] = [
    {
      key: 'country',
      label: 'Target study country',
      done: !!visa?.target_study_country,
      value: visa?.target_study_country ?? undefined,
      to: '/s/profile',
    },
    {
      key: 'status',
      label: 'Current immigration status',
      done: !!visa?.current_immigration_status,
      value: visa?.current_immigration_status ?? undefined,
      to: '/s/profile',
    },
    {
      key: 'english',
      label: 'English proficiency test',
      done: !!englishTest,
      value: englishLabel,
      to: '/s/profile?tab=academics',
    },
    {
      key: 'finances',
      label: 'Proof of finances',
      done: !!visa?.financial_proof_available,
      value: visa?.financial_proof_available ? 'Ready' : undefined,
      to: '/s/profile',
    },
    {
      key: 'passport',
      label: 'Passport on file',
      done: !!visa?.passport_expiration_date,
      value: visa?.passport_expiration_date
        ? `Valid to ${new Date(visa.passport_expiration_date).toLocaleDateString(undefined, { month: 'short', year: 'numeric' })}`
        : undefined,
      to: '/s/profile',
    },
  ]

  const doneCount = items.filter(i => i.done).length

  return (
    <div className="rounded-xl border border-border bg-card p-5">
      <div className="flex items-center justify-between gap-2">
        <p className="flex items-center gap-1.5 text-sm font-bold text-foreground">
          <ListChecks size={15} className="text-secondary" aria-hidden /> Your readiness
        </p>
        <span className="text-xs text-muted-foreground">{doneCount}/{items.length} on file</span>
      </div>
      <p className="mt-1 text-[13px] text-muted-foreground">From your profile — fill any gaps to sharpen your plan.</p>

      <ul className="mt-3 divide-y divide-border">
        {items.map(it => (
          <li key={it.key} className="flex items-center gap-3 py-2.5">
            {it.done ? (
              <Check size={15} className="shrink-0 text-success" aria-hidden />
            ) : (
              <CircleDashed size={15} className="shrink-0 text-muted-foreground" aria-hidden />
            )}
            <span className="min-w-0 flex-1">
              <span className="block text-[13px] font-medium text-foreground">{it.label}</span>
              {it.value && <span className="block truncate text-xs text-muted-foreground">{it.value}</span>}
            </span>
            {!it.done && (
              <button
                onClick={() => navigate(it.to)}
                className="shrink-0 text-xs font-semibold text-secondary hover:underline"
              >
                Add in Profile →
              </button>
            )}
          </li>
        ))}
      </ul>
    </div>
  )
}
