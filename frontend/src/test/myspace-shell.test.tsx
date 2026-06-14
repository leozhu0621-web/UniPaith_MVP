// My Space rail restructure (Spec 2026-06-14) — rooms grouped by content type
// (Record / Collections / Workspace), not application-journey phase.
import { describe, it, expect, vi } from 'vitest'
import { render, screen, within } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

vi.mock('../components/ui/Coachmark', () => ({ default: ({ children }: { children: React.ReactNode }) => children }))
vi.mock('../api/inbox', () => ({ getThreads: vi.fn(() => Promise.resolve([])) }))
vi.mock('../api/applications', () => ({ listMyApplications: vi.fn(() => Promise.resolve([])) }))

import MySpaceShell from '../pages/student/myspace/MySpaceShell'

function renderShell() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter initialEntries={['/s/space']}>
        <MySpaceShell />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('MySpaceShell rail structure', () => {
  it('labels groups by content type, not journey phase', () => {
    renderShell()
    const rail = screen.getByRole('complementary', { name: 'My Space' })
    for (const label of ['Record', 'Collections', 'Workspace']) {
      expect(within(rail).getByText(label)).toBeTruthy()
    }
    for (const phase of ['Plan', 'Prepare', 'Apply & decide', 'Anytime']) {
      expect(within(rail).queryByText(phase)).toBeNull()
    }
  })

  it('keeps all 7 rooms with their existing routes', () => {
    renderShell()
    const rail = screen.getByRole('complementary', { name: 'My Space' })
    const expected: Record<string, string> = {
      Home: '/s/space',
      Profile: '/s/profile',
      Saved: '/s/saved',
      Applications: '/s/applications',
      Prep: '/s/prep',
      Calendar: '/s/calendar',
      Messages: '/s/messages',
    }
    for (const [label, href] of Object.entries(expected)) {
      expect(within(rail).getByRole('link', { name: new RegExp(`^${label}`) }).getAttribute('href')).toBe(href)
    }
  })

  it('orders the rail Home → Profile → Saved → Applications → Prep → Calendar → Messages', () => {
    renderShell()
    const rail = screen.getByRole('complementary', { name: 'My Space' })
    const order = within(rail)
      .getAllByRole('link')
      .map(a => (a.textContent ?? '').trim())
    expect(order).toEqual(['Home', 'Profile', 'Saved', 'Applications', 'Prep', 'Calendar', 'Messages'])
  })
})
