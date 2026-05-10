/**
 * Workshops → Test prep guidance (gap analysis, NO QUESTION GENERATION).
 *
 * Student picks test + scores; backend returns rubric (current vs target +
 * gap) and missing-element prompts (band-classified prep recommendations).
 */
import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'

import {
  type StandardizedTest,
  requestTestGuidance,
} from '../../../api/workshops-feedback'
import Badge from '../../../components/ui/Badge'
import Button from '../../../components/ui/Button'
import Card from '../../../components/ui/Card'
import { showToast } from '../../../stores/toast-store'
import type { WorkshopFeedbackRun } from '../../../types'

const TESTS: StandardizedTest[] = [
  'GRE',
  'GMAT',
  'TOEFL',
  'IELTS',
  'MCAT',
  'LSAT',
  'SAT',
  'ACT',
]

export default function TestGuidancePanel() {
  const [testType, setTestType] = useState<StandardizedTest>('GRE')
  const [current, setCurrent] = useState('')
  const [target, setTarget] = useState('')
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
      showToast((err as Error).message ?? 'Could not generate guidance.', 'error'),
  })

  return (
    <div className="space-y-4">
      <Card className="space-y-3">
        <div>
          <label className="block text-sm font-medium text-student-ink mb-1">Test</label>
          <div className="flex flex-wrap gap-1">
            {TESTS.map(t => (
              <button
                key={t}
                onClick={() => setTestType(t)}
                className={`px-3 py-1.5 text-xs rounded-lg border transition-colors ${
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
            <label className="block text-sm font-medium text-student-ink mb-1">
              Current score
            </label>
            <input
              type="number"
              className="w-full rounded border border-divider px-3 py-2 text-sm"
              value={current}
              onChange={e => setCurrent(e.target.value)}
              min={0}
              max={2000}
              placeholder="e.g., 305"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-student-ink mb-1">
              Target score
            </label>
            <input
              type="number"
              className="w-full rounded border border-divider px-3 py-2 text-sm"
              value={target}
              onChange={e => setTarget(e.target.value)}
              min={0}
              max={2000}
              placeholder="e.g., 320"
            />
          </div>
        </div>
        <div className="text-xs text-student-text">
          You'll get a structured prep plan (small / medium / large gap classification). I won't
          generate practice questions — that's your prep service's job.
        </div>
        <div className="flex justify-end">
          <Button onClick={() => guidanceMut.mutate()} loading={guidanceMut.isPending}>
            Get guidance
          </Button>
        </div>
      </Card>

      {run && (
        <>
          {Object.keys(run.rubric_scores).length > 0 && (
            <Card>
              <div className="text-xs uppercase tracking-wide text-student-text mb-2">
                Gap analysis
              </div>
              <div className="grid grid-cols-3 gap-3">
                {Object.entries(run.rubric_scores).map(([k, v]) => (
                  <div key={k}>
                    <div className="text-xs text-student-text uppercase tracking-wide">
                      {k.replace(/_/g, ' ')}
                    </div>
                    <div className="text-2xl font-semibold text-student-ink">
                      {Number(v)}
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          )}

          {run.missing_elements.length > 0 && (
            <Card>
              <div className="text-xs uppercase tracking-wide text-student-text mb-2">
                Prep recommendations
              </div>
              <ul className="space-y-2">
                {run.missing_elements.map((m, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm">
                    <Badge
                      variant={
                        m.importance === 'required'
                          ? 'danger'
                          : m.importance === 'should_have'
                            ? 'warning'
                            : 'neutral'
                      }
                      size="sm"
                    >
                      {m.importance.replace(/_/g, ' ')}
                    </Badge>
                    <span className="text-student-ink flex-1">{m.element}</span>
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
