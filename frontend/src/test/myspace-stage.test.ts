import { describe, expect, it } from 'vitest'
import { deriveStage, STAGES, type StageInputs } from '../pages/student/myspace/home/journeyStage'

const base: StageInputs = { savedCount: 0, appCount: 0, hasDecision: false, hasOffer: false }

describe('deriveStage', () => {
  it('defaults to Discover with no signals', () => {
    expect(deriveStage(base)).toBe('discover')
  })
  it('reaches Match when programs are saved', () => {
    expect(deriveStage({ ...base, savedCount: 3 })).toBe('match')
  })
  it('reaches Apply when an application exists', () => {
    expect(deriveStage({ ...base, savedCount: 3, appCount: 1 })).toBe('apply')
  })
  it('reaches Decide on a decision or offer', () => {
    expect(deriveStage({ ...base, appCount: 2, hasOffer: true })).toBe('decide')
    expect(deriveStage({ ...base, appCount: 2, hasDecision: true })).toBe('decide')
  })
  it('exposes the four ordered stages', () => {
    expect(STAGES.map(s => s.key)).toEqual(['discover', 'match', 'apply', 'decide'])
  })
})
