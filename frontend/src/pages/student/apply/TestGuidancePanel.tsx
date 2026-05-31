/**
 * Workshops → Test prep guidance (gap analysis, NO QUESTION GENERATION).
 *
 * The student picks a test + scores; the backend returns a gap analysis
 * (current vs target vs gap) plus band-classified prep recommendations and,
 * on the AI path, section diagnoses + resource categories. It never generates
 * practice questions or answers (Spec/14-workshops.md §5).
 */
import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'

import { type StandardizedTest, requestTestGuidance } from '../../../api/workshops-feedback'
import Badge from '../../../components/ui/Badge'
import Button from '../../../components/ui/Button'
import Card from '../../../components/ui/Card'
import { showToast } from '../../../stores/toast-store'
import type { WorkshopFeedbackRun } from '../../../types'

import { EmptyHint, ErrorNote, ReadinessCard, StubNote } from './WorkshopShared'
import WorkshopProgramPicker, {
  type ProgramOption,
  type WorkshopMode,
} from './WorkshopProgramPicker'
import { IMPORTANCE_VARIANT, SEVERITY_VARIANT, readinessSummary } from './workshopReadiness'

const TESTS: StandardizedTest[] = ['GRE', 'GMAT', 'TOEFL', 'IELTS', 'MCAT', 'LSAT', 'SAT', 'ACT']

const STAT_LABEL: Record<string, string> = {
  current_score: 'Current',
  target_score: 'Target',
  gap: 'Gap',
}

export default function TestGuidancePanel() {
  const [testType, setTestType] = useState<StandardizedTest>('GRE')
  const [current, setCurrent] = useState('')
  const [target, setTarget] = useState('')
  const [mode, setMode] = useState<WorkshopMode>('general')
  const [program, setProgram] = useState<ProgramOption | null>(null)
  const [run, setRun] = useState<WorkshopFeedbackRun | null>(null)

  const guidanceMut = useMutation({
    mutationFn: () =>
      requestTestGuidance({
        test_type: testType,
        current_score: current ? Number(current) : null,
        target_score: target ? Number(target) : null,
      }),
    onSuccess: r => {
      setRun(r)
      showToast('Guidance ready.', 'success')
    },
    onError: (err: unknown) =>
      showToast((err as Error).message ?? 'Could not get guidance.', 'error'),
  })

  const stats = run ? Object.entries(run.rubric_scores ?? {}) : []
  const readiness =
    run && mode === 'program_specific' && program
      ? readinessSummary(run, program.programName)
      : null

  return (
    <div className="space-y-4">
      <Card className="space-y-3">
        <WorkshopProgramPicker
          mode={mode}
          onModeChange={setMode}
          program={program}
          onProgramChange={setProgram}
        />

        <div>
          <label className="mb-1 block text-sm font-medium text-student-ink">Test</label>
          <div className="flex flex-wrap gap-1">
            {TESTS.map(t => (
              <button
                key={t}
                type="button"
                onClick={() => setTestType(t)}
                className={`rounded-lg border px-3 py-1.5 text-xs transition-colors ${
                  testType === t
                    ? 'border-student bg-student/5 text-student-ink'
                    : 'border-divider text-student-text hover:border-student-text'
                }`}
              >
                {t}
              </button>
            ))}
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="mb-1 block text-sm font-medium text-student-ink">Current score</label>
            <input
              type="number"
              className="w-full rounded-md border border-divider px-3 py-2 text-sm"
              value={current}
              onChange={e => setCurrent(e.target.value)}
              min={0}
              max={2000}
              placeholder="e.g., 305"
            />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-student-ink">Target score</label>
            <input
              type="number"
              className="w-full rounded-md border border-divider px-3 py-2 text-sm"
              value={target}
              onChange={e => setTarget(e.target.value)}
              min={0}
              max={2000}
              placeholder="e.g., 320"
            />
          </div>
        </div>

        <div className="text-xs text-student-text">
          You'll get a structured prep plan (small / medium / large gap). I won't generate practice
          questions — that's your prep service's job.
        </div>

        <div className="flex justify-end">
          <Button
            variant="secondary"
            onClick={() => guidanceMut.mutate()}
            loading={guidanceMut.isPending}
          >
            Get guidance
          </Button>
        </div>
      </Card>

      {!run && !guidanceMut.isPending && !guidanceMut.isError && (
        <EmptyHint>Add your current and target scores to get a structured prep plan.</EmptyHint>
      )}

      {guidanceMut.isError && !run && <ErrorNote onRetry={() => guidanceMut.mutate()} />}

      {run && (
        <>
          {readiness && program && (
            <ReadinessCard programName={program.programName} summary={readiness} />
          )}

          {stats.length > 0 && (
            <Card>
              <div className="mb-2 flex items-center justify-between">
                <div className="text-eyebrow uppercase text-student-text">Gap analysis</div>
                {run.is_stub && <StubNote />}
              </div>
              <div className="grid grid-cols-3 gap-3">
                {stats.map(([k, v]) => (
                  <div key={k}>
                    <div className="text-eyebrow uppercase text-student-text">
                      {STAT_LABEL[k] ?? k.replace(/_/g, ' ')}
                    </div>
                    <div className="text-2xl font-semibold text-student-ink">{Number(v)}</div>
                  </div>
                ))}
              </div>
            </Card>
          )}

          {run.structural_issues.length > 0 && (
            <Card>
              <div className="mb-2 text-eyebrow uppercase text-student-text">
                Section diagnosis · {run.structural_issues.length}
              </div>
              <ul className="space-y-2">
                {run.structural_issues.map((iss, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm">
                    <Badge variant={SEVERITY_VARIANT[iss.severity]} size="sm">
                      {iss.severity}
                    </Badge>
                    <div className="flex-1">
                      <div className="text-student-ink">{iss.issue}</div>
                      {iss.location_ref && (
                        <div className="mt-0.5 text-xs text-student-text">{iss.location_ref}</div>
                      )}
                    </div>
                  </li>
                ))}
              </ul>
            </Card>
          )}

          {run.missing_elements.length > 0 && (
            <Card>
              <div className="mb-2 text-eyebrow uppercase text-student-text">
                Prep recommendations · {run.missing_elements.length}
              </div>
              <ul className="space-y-2">
                {run.missing_elements.map((m, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm">
                    <Badge variant={IMPORTANCE_VARIANT[m.importance]} size="sm">
                      {m.importance.replace(/_/g, ' ')}
                    </Badge>
                    <span className="flex-1 text-student-ink">{m.element}</span>
                  </li>
                ))}
              </ul>
            </Card>
          )}

          {run.suggested_questions.length > 0 && (
            <Card>
              <div className="mb-2 text-eyebrow uppercase text-student-text">
                Suggested resources · {run.suggested_questions.length}
              </div>
              <ul className="space-y-2">
                {run.suggested_questions.map((q, i) => (
                  <li key={i} className="text-sm">
                    <div className="text-student-ink">{q.question}</div>
                    {q.why && <div className="mt-0.5 text-xs italic text-student-text">{q.why}</div>}
                  </li>
                ))}
              </ul>
            </Card>
          )}
        </>
      )}
    </div>
  )
}
