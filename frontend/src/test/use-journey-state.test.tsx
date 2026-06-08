import { describe, it, expect } from 'vitest'
import { deriveStages } from '../pages/student/discover/useJourneyState'

describe('deriveStages', () => {
  it('marks first incomplete as current, prior as done, later as locked', () => {
    const s = deriveStages({ profile: '0.8', goals: '0.2', needs: '0' })
    expect(s.map(x => [x.key, x.state])).toEqual([
      ['profile', 'done'],
      ['goals', 'current'],
      ['needs', 'locked'],
    ])
  })

  it('all done when every layer is ready', () => {
    const s = deriveStages({ profile: '0.6', goals: '0.7', needs: '0.9' })
    expect(s.every(x => x.state === 'done')).toBe(true)
  })

  it('first layer is current when nothing captured yet', () => {
    const s = deriveStages(undefined)
    expect(s.map(x => x.state)).toEqual(['current', 'locked', 'locked'])
  })
})
