import { describe, expect, it } from 'vitest'
import { buildUpNext, type UpNextInputs } from '../pages/student/myspace/home/upNext'

const base: UpNextInputs = {
  calItems: [],
  offers: [],
  drafts: [],
  pendingClarifications: 0,
}

describe('buildUpNext', () => {
  it('orders overdue → offer → interview → draft → clarification and caps at 5', () => {
    const inputs: UpNextInputs = {
      calItems: [
        { id: 'o1', title: 'Late thing', status: 'overdue', subtitle: null, institution_name: 'X', can_confirm: false, start_at: '2026-01-01' },
        { id: 'iv', title: 'Interview', status: 'scheduled', subtitle: null, institution_name: 'Y', can_confirm: true, start_at: '2026-07-01' },
      ] as any,
      offers: [{ id: 'a1', status: 'decision_made', decision: 'admitted', student_decision: null, program: { program_name: 'CS', institution_name: 'MIT' } }] as any,
      drafts: [{ id: 'd1', status: 'draft', readiness_pct: 80, program: { program_name: 'EE' } }] as any,
      pendingClarifications: 2,
    }
    const out = buildUpNext(inputs)
    expect(out.map(a => a.chip)).toEqual(['overdue', 'offer in', 'slots held', 'draft', 'quick win'])
    expect(out.length).toBeLessThanOrEqual(5)
  })

  it('returns [] when nothing is pending', () => {
    expect(buildUpNext(base)).toEqual([])
  })

  it('drops offers the student already decided on', () => {
    const out = buildUpNext({ ...base, offers: [{ id: 'a', status: 'decision_made', decision: 'admitted', student_decision: 'accepted_by_student', program: {} }] as any })
    expect(out).toEqual([])
  })
})
