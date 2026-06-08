import { describe, it, expect } from 'vitest'
import { ROUTE_TITLES } from '../components/layout/StudentTitle'

describe('Discover → Uni rename', () => {
  it('routes /s to the "Uni" title', () => {
    expect(ROUTE_TITLES['/s']).toBe('Uni')
  })
  it('has no stray "Discover" surface title', () => {
    expect(Object.values(ROUTE_TITLES)).not.toContain('Discover')
  })
})
