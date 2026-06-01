import { describe, it, expect } from 'vitest'
import {
  decisionLabel,
  formatOfferTermsSummary,
  isOfferDecision,
  INSTITUTION_DECISIONS,
} from '../pages/institution/pipeline/decisionUtils'

/** Spec 34 — institution decisions UI helpers (copy, offer summary, restrained tones). */
describe('spec34 institution decision utils', () => {
  it('maps all five institution decision types', () => {
    expect(INSTITUTION_DECISIONS.map(d => d.value)).toEqual([
      'admitted',
      'conditional_admission',
      'waitlisted',
      'deferred',
      'rejected',
    ])
  })

  it('uses spec copy for response states via decision labels', () => {
    expect(decisionLabel('admitted')).toBe('Admit')
    expect(decisionLabel('waitlisted')).toBe('Waitlist')
  })

  it('detects offer-producing decisions', () => {
    expect(isOfferDecision('admitted')).toBe(true)
    expect(isOfferDecision('conditional_admission')).toBe(true)
    expect(isOfferDecision('rejected')).toBe(false)
  })

  it('formats offer terms for confirm modal (§8)', () => {
    const lines = formatOfferTermsSummary({
      offer_type: 'full_admission',
      scholarship_amount: 15000,
      response_deadline: '2027-04-15',
      start_term: { season: 'Fall', year: 2027 },
    })
    expect(lines.some(l => l.includes('Scholarship'))).toBe(true)
    expect(lines.some(l => l.includes('Respond by'))).toBe(true)
    expect(lines.some(l => l.includes('Fall 2027'))).toBe(true)
  })
})
