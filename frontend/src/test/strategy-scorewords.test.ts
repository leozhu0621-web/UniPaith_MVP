import { describe, expect, it } from 'vitest'

import { fitWord, oddsWord } from '../pages/student/profile/strategy/scoreWords'

describe('fitWord — fitness_score → fit word', () => {
  it('returns null for absent / zero scores', () => {
    expect(fitWord(null)).toBeNull()
    expect(fitWord(undefined)).toBeNull()
    expect(fitWord(0)).toBeNull()
    expect(fitWord('0')).toBeNull()
    expect(fitWord(NaN)).toBeNull()
    expect(fitWord('not-a-number')).toBeNull()
    expect(fitWord(-0.3)).toBeNull()
  })

  it('maps the band boundaries', () => {
    expect(fitWord(0.85)).toBe('Excellent fit')
    expect(fitWord(0.9)).toBe('Excellent fit')
    expect(fitWord(0.7)).toBe('Strong fit')
    expect(fitWord(0.84)).toBe('Strong fit')
    expect(fitWord(0.55)).toBe('Good fit')
    expect(fitWord(0.69)).toBe('Good fit')
    expect(fitWord(0.4)).toBe('Moderate fit')
    expect(fitWord(0.54)).toBe('Moderate fit')
    expect(fitWord(0.39)).toBe('Low fit')
    expect(fitWord(0.1)).toBe('Low fit')
  })

  it('coerces string scores', () => {
    expect(fitWord('0.85')).toBe('Excellent fit')
    expect(fitWord('0.55')).toBe('Good fit')
    expect(fitWord('0.2')).toBe('Low fit')
  })
})

describe('oddsWord — confidence_score → odds word', () => {
  it('returns null for absent / zero scores', () => {
    expect(oddsWord(null)).toBeNull()
    expect(oddsWord(undefined)).toBeNull()
    expect(oddsWord(0)).toBeNull()
    expect(oddsWord('0')).toBeNull()
    expect(oddsWord(NaN)).toBeNull()
    expect(oddsWord('')).toBeNull()
  })

  it('maps the band boundaries', () => {
    expect(oddsWord(0.8)).toBe('Safe')
    expect(oddsWord(0.95)).toBe('Safe')
    expect(oddsWord(0.6)).toBe('Likely')
    expect(oddsWord(0.79)).toBe('Likely')
    expect(oddsWord(0.4)).toBe('Toss-up')
    expect(oddsWord(0.59)).toBe('Toss-up')
    expect(oddsWord(0.2)).toBe('Reach')
    expect(oddsWord(0.39)).toBe('Reach')
    expect(oddsWord(0.19)).toBe('Long shot')
    expect(oddsWord(0.05)).toBe('Long shot')
  })

  it('coerces string scores', () => {
    expect(oddsWord('0.8')).toBe('Safe')
    expect(oddsWord('0.4')).toBe('Toss-up')
    expect(oddsWord('0.1')).toBe('Long shot')
  })
})
