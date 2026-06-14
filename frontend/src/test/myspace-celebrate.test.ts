import { beforeEach, describe, expect, it } from 'vitest'
import { freshWinIds, markCelebrated, CELEBRATE_KEY } from '../pages/student/myspace/home/celebrate'

describe('celebrate', () => {
  beforeEach(() => localStorage.clear())

  it('returns all ids on first sight, none after marking', () => {
    expect(freshWinIds(['offer-a', 'offer-b'])).toEqual(['offer-a', 'offer-b'])
    markCelebrated(['offer-a', 'offer-b'])
    expect(freshWinIds(['offer-a', 'offer-b'])).toEqual([])
  })

  it('only the new id is fresh after a prior celebration', () => {
    markCelebrated(['offer-a'])
    expect(freshWinIds(['offer-a', 'offer-b'])).toEqual(['offer-b'])
  })

  it('survives malformed storage', () => {
    localStorage.setItem(CELEBRATE_KEY, 'not json')
    expect(freshWinIds(['x'])).toEqual(['x'])
  })
})
