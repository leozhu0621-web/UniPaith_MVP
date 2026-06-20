// Applied-status pill on discovery cards (Discover review 2026-06-19, benchmark
// lens). Pins the honest-stage labelling: a real application stage shows a pill;
// no application shows nothing (no fabricated status).
import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import AppStatusPill from '../pages/student/explore/cards/AppStatusPill'

describe('AppStatusPill', () => {
  it('labels a submitted application "Applied"', () => {
    render(<AppStatusPill status="submitted" />)
    expect(screen.getByText('Applied')).toBeInTheDocument()
  })

  it('shows the real downstream stage, not a generic label', () => {
    const { rerender } = render(<AppStatusPill status="under_review" />)
    expect(screen.getByText('In review')).toBeInTheDocument()
    rerender(<AppStatusPill status="interview" />)
    expect(screen.getByText('Interview')).toBeInTheDocument()
    rerender(<AppStatusPill status="decision_made" />)
    expect(screen.getByText('Decision')).toBeInTheDocument()
  })

  it('marks a not-yet-submitted application as a Draft (not "Applied")', () => {
    render(<AppStatusPill status="draft" />)
    expect(screen.getByText('Draft')).toBeInTheDocument()
    expect(screen.queryByText('Applied')).not.toBeInTheDocument()
  })

  it('renders nothing when there is no application (no fabricated status)', () => {
    const { container } = render(<AppStatusPill status={null} />)
    expect(container).toBeEmptyDOMElement()
  })
})
