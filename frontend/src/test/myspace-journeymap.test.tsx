import { describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import JourneyMap from '../pages/student/myspace/home/JourneyMap'

const renderMap = (props: React.ComponentProps<typeof JourneyMap>) =>
  render(<MemoryRouter><JourneyMap {...props} /></MemoryRouter>)

describe('JourneyMap', () => {
  it('marks the derived current stage with aria-current', () => {
    renderMap({ savedCount: 2, appCount: 0, hasDecision: false, hasOffer: false })
    expect(screen.getByText('Match').closest('[aria-current="step"]')).not.toBeNull()
  })
  it('renders all four stage labels', () => {
    renderMap({ savedCount: 0, appCount: 0, hasDecision: false, hasOffer: false })
    for (const label of ['Discover', 'Match', 'Apply', 'Decide']) {
      expect(screen.getByText(label)).toBeTruthy()
    }
  })
})
