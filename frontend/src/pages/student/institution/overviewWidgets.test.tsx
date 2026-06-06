import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { AdmissionsFunnel, ChipList, DiversityBar, RankingBadge, StatBar } from './overviewWidgets'

describe('RankingBadge', () => {
  it('renders the rank and label', () => {
    render(<RankingBadge rank={1} label="QS World University Rankings" year={2025} peak />)
    expect(screen.getByText('#1')).toBeInTheDocument()
    expect(screen.getByText(/QS World University Rankings/)).toBeInTheDocument()
  })

  it('marks the #1 peak with the gold treatment, and non-peak without it', () => {
    const { rerender } = render(<RankingBadge rank={1} label="QS" peak />)
    expect(screen.getByTestId('ranking-badge')).toHaveAttribute('data-peak', 'true')
    rerender(<RankingBadge rank={2} label="Times Higher Education" />)
    expect(screen.getByTestId('ranking-badge')).not.toHaveAttribute('data-peak')
  })
})

describe('AdmissionsFunnel', () => {
  it('shows applied, admitted, the acceptance rate, and the cycle', () => {
    render(<AdmissionsFunnel applicants={29281} admits={1334} rate={0.0455} cycle="Class of 2029" />)
    expect(screen.getByText('29,281')).toBeInTheDocument()
    expect(screen.getByText('1,334')).toBeInTheDocument()
    expect(screen.getByText('4.5%')).toBeInTheDocument()
    expect(screen.getByText('Class of 2029')).toBeInTheDocument()
  })
})

describe('DiversityBar', () => {
  it('renders a legend entry per non-zero segment and drops zeros', () => {
    render(
      <DiversityBar
        segments={[
          { label: 'Asian', pct: 0.35 },
          { label: 'White', pct: 0.21 },
          { label: 'Hispanic', pct: 0 },
        ]}
      />,
    )
    expect(screen.getByText('Asian')).toBeInTheDocument()
    expect(screen.getByText('White')).toBeInTheDocument()
    expect(screen.getByText('35%')).toBeInTheDocument()
    expect(screen.queryByText('Hispanic')).not.toBeInTheDocument()
  })

  it('returns null when there are no segments', () => {
    const { container } = render(<DiversityBar segments={[]} />)
    expect(container).toBeEmptyDOMElement()
  })
})

describe('StatBar', () => {
  it('renders the label and the rounded percent', () => {
    render(<StatBar label="Pell grant recipients" pct={0.1932} />)
    expect(screen.getByText('Pell grant recipients')).toBeInTheDocument()
    expect(screen.getByText('19%')).toBeInTheDocument()
  })
})

describe('ChipList', () => {
  it('renders one chip per item', () => {
    render(<ChipList items={['Technology', 'Finance', 'Consulting']} />)
    expect(screen.getByText('Technology')).toBeInTheDocument()
    expect(screen.getByText('Finance')).toBeInTheDocument()
    expect(screen.getByText('Consulting')).toBeInTheDocument()
  })

  it('returns null when empty', () => {
    const { container } = render(<ChipList items={[]} />)
    expect(container).toBeEmptyDOMElement()
  })
})
