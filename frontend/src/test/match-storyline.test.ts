import { describe, it, expect } from 'vitest'

import { matchStoryline } from '../pages/student/match/matchStoryline'

describe('matchStoryline', () => {
  it('frames a reach as strong fit but competitive odds', () => {
    expect(matchStoryline('reach', 0.82, true)).toBe(
      'Strong fit for you — but admission here is competitive.',
    )
  })

  it('frames a target as fit + realistic odds (additive, not a contrast)', () => {
    expect(matchStoryline('target', 0.8, true)).toBe(
      'Strong fit for you, and your odds look realistic.',
    )
  })

  it('frames a safer choice as fit + very likely in', () => {
    expect(matchStoryline('safer', 0.78, true)).toContain("very likely to get in")
  })

  it('tiers the fit phrase by the fitness score', () => {
    expect(matchStoryline('reach', 0.55, true)).toMatch(/^A solid fit/)
    expect(matchStoryline('reach', 0.3, true)).toMatch(/^A fair fit/)
  })

  it('uses the tier boundaries 0.7 (high) and 0.45 (mid)', () => {
    expect(matchStoryline('target', 0.7, true)).toMatch(/^Strong fit/)
    expect(matchStoryline('target', 0.69, true)).toMatch(/^A solid fit/)
    expect(matchStoryline('target', 0.45, true)).toMatch(/^A solid fit/)
    expect(matchStoryline('target', 0.44, true)).toMatch(/^A fair fit/)
  })

  it('falls back to a band-only, odds-framed line when fitness is unknown', () => {
    expect(matchStoryline('reach', 0, false)).toBe('A reach — admission here is competitive.')
    expect(matchStoryline('target', 0, false)).toBe('A target — your odds look realistic.')
    expect(matchStoryline('safer', 0, false)).toBe(
      "A safer choice — you're very likely to get in.",
    )
  })

  it('returns an empty string when the band is unknown (no line to show)', () => {
    expect(matchStoryline(null, 0.8, true)).toBe('')
    expect(matchStoryline(undefined, 0.8, true)).toBe('')
  })
})
