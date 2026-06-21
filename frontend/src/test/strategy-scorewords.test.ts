import { describe, expect, it } from 'vitest'

import { fitWord, oddsWord } from '../pages/student/profile/strategy/scoreWords'

describe('fitWord — fitness_score → fit word (Discover tiers)', () => {
  it('returns null for absent / zero / invalid scores', () => {
    expect(fitWord(null)).toBeNull()
    expect(fitWord(undefined)).toBeNull()
    expect(fitWord(0)).toBeNull()
    expect(fitWord('0')).toBeNull()
    expect(fitWord(NaN)).toBeNull()
    expect(fitWord('not-a-number')).toBeNull()
    expect(fitWord(-0.3)).toBeNull()
  })

  it('maps the 0.7 / 0.45 boundaries (matching matchStoryline)', () => {
    expect(fitWord(0.9)).toBe('Strong fit')
    expect(fitWord(0.7)).toBe('Strong fit')
    expect(fitWord(0.69)).toBe('Solid fit')
    expect(fitWord(0.45)).toBe('Solid fit')
    expect(fitWord(0.44)).toBe('Fair fit')
    expect(fitWord(0.1)).toBe('Fair fit')
  })

  it('coerces string scores', () => {
    expect(fitWord('0.8')).toBe('Strong fit')
    expect(fitWord('0.5')).toBe('Solid fit')
    expect(fitWord('0.2')).toBe('Fair fit')
  })
})

describe('oddsWord — band_label → odds word (Discover signal)', () => {
  it('returns null for an absent band', () => {
    expect(oddsWord(null)).toBeNull()
    expect(oddsWord(undefined)).toBeNull()
  })

  it('maps each admission band', () => {
    expect(oddsWord('reach')).toBe('Reach')
    expect(oddsWord('target')).toBe('Target')
    expect(oddsWord('safer')).toBe('Safer')
  })
})
