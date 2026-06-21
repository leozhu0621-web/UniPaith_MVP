import { describe, it, expect } from 'vitest'

import { shortlistDigest } from '../pages/student/match/shortlistDigest'
import type { MatchResultDual } from '../types'

function m(band: string, fitness: string | null, name = 'P', inst = 'U'): MatchResultDual {
  return {
    band_label: band,
    fitness_score: fitness,
    program_name: name,
    institution_name: inst,
  } as unknown as MatchResultDual
}

describe('shortlistDigest', () => {
  it('returns null for an empty list', () => {
    expect(shortlistDigest([])).toBeNull()
  })

  it('counts by band and totals', () => {
    const d = shortlistDigest([m('reach', '0.8'), m('reach', '0.7'), m('target', '0.6'), m('safer', '0.5')])!
    expect(d.total).toBe(4)
    expect(d.counts).toEqual({ reach: 2, target: 1, safer: 1 })
  })

  it('treats a missing band as target', () => {
    const d = shortlistDigest([m('reach', '0.8'), m('', '0.6')])!
    expect(d.counts.target).toBe(1)
  })

  it('reads a balanced shortlist', () => {
    const d = shortlistDigest([m('reach', '0.8'), m('reach', '0.7'), m('reach', '0.6'), m('target', '0.6'), m('target', '0.6'), m('safer', '0.5'), m('safer', '0.5')])!
    expect(d.balance).toBe('balanced')
  })

  it('flags a reach-heavy list (reaches outnumber the rest, ≥2)', () => {
    const d = shortlistDigest([m('reach', '0.8'), m('reach', '0.7'), m('reach', '0.6'), m('target', '0.6')])!
    expect(d.balance).toBe('reach_heavy')
  })

  it('flags a safe-heavy list', () => {
    const d = shortlistDigest([m('safer', '0.8'), m('safer', '0.7'), m('safer', '0.6'), m('target', '0.6')])!
    expect(d.balance).toBe('safe_heavy')
  })

  it('picks the highest-fitness match as the standout', () => {
    const d = shortlistDigest([m('target', '0.61', 'Mid'), m('reach', '0.92', 'Top'), m('safer', '0.40', 'Low')])!
    expect(d.standout?.program_name).toBe('Top')
  })

  it('handles a list with no fitness scores (standout falls back, no crash)', () => {
    const d = shortlistDigest([m('target', null, 'A'), m('reach', null, 'B')])!
    expect(d.total).toBe(2)
    expect(d.standout).not.toBeNull()
  })
})
