import { describe, expect, it } from 'vitest'

import {
  IMPORTANCE_VARIANT,
  SEVERITY_VARIANT,
  readinessSummary,
} from '../pages/student/apply/workshopReadiness'
import type { WorkshopFeedbackRun } from '../types'

function makeRun(partial: Partial<WorkshopFeedbackRun>): WorkshopFeedbackRun {
  return {
    id: 'r1',
    student_id: 's1',
    domain: 'essay',
    input_artifact_id: null,
    prompt_text: null,
    rubric_scores: {},
    structural_issues: [],
    missing_elements: [],
    suggested_questions: [],
    is_stub: true,
    created_at: '2026-01-01T00:00:00Z',
    ...partial,
  }
}

describe('Spec 14 — workshop feedback (feedback-only) helpers', () => {
  it('maps severity + importance to design-system alert variants (Spec/02 §11)', () => {
    expect(SEVERITY_VARIANT.major).toBe('danger')
    expect(SEVERITY_VARIANT.moderate).toBe('warning')
    expect(SEVERITY_VARIANT.minor).toBe('neutral')
    expect(IMPORTANCE_VARIANT.required).toBe('danger')
    expect(IMPORTANCE_VARIANT.should_have).toBe('warning')
    expect(IMPORTANCE_VARIANT.nice_to_have).toBe('neutral')
  })

  it('essay readiness names the strongest + weakest rubric dimension', () => {
    const run = makeRun({
      domain: 'essay',
      rubric_scores: { clarity: 5, structure: 3, evidence: 4, specificity: 2 },
    })
    const summary = readinessSummary(run, 'Foo CS MS')
    expect(summary).toContain('Foo CS MS')
    expect(summary).toContain('strongest on clarity')
    expect(summary).toContain('focus on specificity')
  })

  it('essay readiness flags required missing elements', () => {
    const run = makeRun({
      domain: 'essay',
      rubric_scores: { clarity: 4, structure: 4 },
      missing_elements: [{ element: 'first-person voice', importance: 'required' }],
    })
    expect(readinessSummary(run, 'Bar')).toContain('1 required element to add')
  })

  it('test readiness classifies the score gap into bands', () => {
    const small = readinessSummary(
      makeRun({ domain: 'test', rubric_scores: { current_score: 310, target_score: 320, gap: 10 } }),
      'Grad School',
    )
    expect(small).toContain('a small gap')

    const large = readinessSummary(
      makeRun({ domain: 'test', rubric_scores: { current_score: 150, target_score: 330, gap: 180 } }),
      'Grad School',
    )
    expect(large).toContain('a large gap')

    const met = readinessSummary(
      makeRun({ domain: 'test', rubric_scores: { current_score: 330, target_score: 320, gap: -10 } }),
      'Grad School',
    )
    expect(met).toContain('at or above target')
  })

  it('returns null when there is nothing meaningful to summarize', () => {
    expect(readinessSummary(makeRun({ domain: 'essay', rubric_scores: {} }), 'X')).toBeNull()
  })
})
