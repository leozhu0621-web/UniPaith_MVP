import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { vi } from 'vitest'

import PricingPage from '../pages/public/PricingPage'
import AboutPage from '../pages/public/AboutPage'

// Spec 07 (Product Context) — pricing/about surfaces. Mock the public plan
// catalog so the data-driven pricing page renders deterministically.
vi.mock('../hooks/useSubscription', () => ({
  usePlans: () => ({
    data: {
      student: {
        id: 'student_pro',
        name: 'UniPaith Pro',
        tagline: 'Everyone’s private college counselor',
        price_monthly: 15,
        currency: 'USD',
        trial_days: 7,
        ad_free_addon_monthly: 5,
      },
      institution: {
        id: 'institution',
        name: 'Institution',
        tagline: 'The admission operating system',
        price_per_applicant: 15,
        currency: 'USD',
        billing_model: 'per_applicant',
      },
      features: [
        { label: 'Portable universal profile', free: true, pro: true },
        { label: 'Expanded matching with full reasoning', free: false, pro: true },
      ],
    },
  }),
}))

function renderAt(node: React.ReactNode) {
  return render(<MemoryRouter>{node}</MemoryRouter>)
}

describe('Spec 07 — Pricing page', () => {
  it('renders the student plan, $15 price, 7-day trial, and the free-vs-pro matrix', () => {
    renderAt(<PricingPage />)
    expect(screen.getByText('UniPaith Pro')).toBeInTheDocument()
    expect(screen.getAllByText(/\$15/).length).toBeGreaterThan(0)
    expect(screen.getAllByText(/7-day free trial/i).length).toBeGreaterThan(0)
    expect(screen.getByText('Free vs Pro')).toBeInTheDocument()
    expect(screen.getAllByText('Expanded matching with full reasoning').length).toBeGreaterThan(0)
    // Both the student and institution plans surface a $15 price point.
    expect(screen.getAllByText('$15').length).toBe(2)
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
