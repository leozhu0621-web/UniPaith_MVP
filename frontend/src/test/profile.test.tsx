/**
 * Universal Profile (spec 10) — layout routing, completion ring, API contract.
 */
import { afterEach, describe, expect, it, vi } from 'vitest'
import { cleanup, render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

// Mock the API so the layout + active Overview tab render without network.
vi.mock('../api/students', async orig => {
  const actual = await orig<typeof import('../api/students')>()
  return {
    ...actual,
    getProfile: () => Promise.resolve({ id: 'p1', preferences: null }),
    getProfileOverview: () =>
      Promise.resolve({
        personal: {
          first_name: 'Sienna',
          last_name: 'Chen',
          preferred_name: null,
          primary_email: 'sienna@example.com',
          preferred_pronouns: null,
          nationality: null,
          country_of_residence: null,
        },
        completion: {
          overall_pct: 42,
          per_category: [
            { category: 'identity', pct: 50, last_updated: null },
            { category: 'academics', pct: 40, last_updated: null },
            { category: 'experience', pct: 20, last_updated: null },
            { category: 'goals', pct: 0, last_updated: null },
            { category: 'needs', pct: 0, last_updated: null },
            { category: 'strategy', pct: 0, last_updated: null },
            { category: 'preparation', pct: 25, last_updated: null },
            { category: 'preferences', pct: 66, last_updated: null },
            { category: 'financial', pct: 33, last_updated: null },
            { category: 'data', pct: 100, last_updated: null },
          ],
        },
        next_actions: [],
      }),
  }
})

import CompletionRing from '../pages/student/profile/CompletionRing'
import ProfilePage from '../pages/student/ProfilePage'
import * as students from '../api/students'

const TAB_LABELS = [
  'Overview', 'Identity', 'Academics', 'Experience', 'Goals', 'Needs', 'Strategy',
  'Preparation', 'Preferences', 'Financial', 'Timeline', 'Analytics', 'Data',
]

function renderPage(initial = '/s/profile') {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter initialEntries={[initial]}>
        <ProfilePage />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

afterEach(cleanup)

describe('Universal Profile layout', () => {
  it('renders the eyebrow, H1, and all 13 tabs', async () => {
    renderPage()
    expect(await screen.findByText('Your record')).toBeTruthy()
    expect(screen.getByText('PROFILE')).toBeTruthy()
    for (const label of TAB_LABELS) {
      expect(screen.getByRole('button', { name: label })).toBeTruthy()
    }
  })

  it('resolves a deep-linked tab (?tab=data) as active', async () => {
    renderPage('/s/profile?tab=data')
    const dataTab = await screen.findByRole('button', { name: 'Data' })
    expect(dataTab.getAttribute('aria-current')).toBe('page')
  })
})

describe('CompletionRing', () => {
  it('shows the rounded percentage', () => {
    render(<CompletionRing value={73} />)
    expect(screen.getByText('73%')).toBeTruthy()
  })
})

describe('Profile API contract', () => {
  it('exposes the new Universal Profile functions', () => {
    expect(typeof students.getProfileOverview).toBe('function')
    expect(typeof students.getAccessLog).toBe('function')
    expect(typeof students.exportProfilePdf).toBe('function')
    expect(typeof students.exportProfileExternal).toBe('function')
  })
})
