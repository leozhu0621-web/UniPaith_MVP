import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'

import PricingPage from '../pages/public/PricingPage'
import AboutPage from '../pages/public/AboutPage'

// Spec 07 — public pricing + positioning pages (static; the billing engine is
// Spec 06's). No mocks needed.
function renderAt(node: React.ReactNode) {
  return render(<MemoryRouter>{node}</MemoryRouter>)
}

describe('Spec 07 — Pricing page', () => {
  it('renders the Plus plan, $15 price, 7-day trial, and the free-vs-plus matrix', () => {
    renderAt(<PricingPage />)
    expect(screen.getByText('UniPaith Plus')).toBeInTheDocument()
    // Both the student (Plus) and institution plans surface a $15 price point.
    expect(screen.getAllByText('$15').length).toBe(2)
    expect(screen.getAllByText(/7-day free trial/i).length).toBeGreaterThan(0)
    expect(screen.getByText('Free vs Plus')).toBeInTheDocument()
  })

  it('surfaces the four brand values', () => {
    renderAt(<PricingPage />)
    expect(screen.getByText('Fit, not fame')).toBeInTheDocument()
    expect(screen.getByText('Explain everything')).toBeInTheDocument()
  })
})

describe('Spec 07 — About page', () => {
  it('renders positioning and the operative brand values', () => {
    renderAt(<AboutPage />)
    expect(screen.getByText(/two-sided, AI-supported admissions layer/i)).toBeInTheDocument()
    expect(screen.getByText('Partnership, not extraction')).toBeInTheDocument()
    expect(screen.getByText('Bias-avoidance is a practice')).toBeInTheDocument()
  })
})
