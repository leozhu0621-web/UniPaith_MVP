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
  it('keeps the content groups in the rail', () => {
    renderShell()
    const rail = screen.getByRole('complementary', { name: 'My Space' })
    for (const label of ['Profile', 'Planning', 'Saved', 'Workspace']) {
      expect(within(rail).getByText(label)).toBeTruthy()
    }
  })

  it('shows Overview and Import as the first two rail links', () => {
    renderShell()
    const rail = screen.getByRole('complementary', { name: 'My Space' })
    const links = within(rail)
      .getAllByRole('link')
      .map(a => (a.getAttribute('href') ?? '').trim())
    // At /s/space no group is expanded, so the only links are the two top-level
    // items — Import sits right after Overview (Spec 2026-06-16).
    expect(links.slice(0, 2)).toEqual(['/s/space', '/s/import'])
  })

  it('points Import at /s/import', () => {
    renderShell()
    const rail = screen.getByRole('complementary', { name: 'My Space' })
    expect(
      within(rail).getByRole('link', { name: /^Import/ }).getAttribute('href'),
    ).toBe('/s/import')
  })

  it('shows named metadata for rail rooms', () => {
    renderShell()
    const rail = screen.getByRole('complementary', { name: 'My Space' })

    expect(within(rail).getByText('What matters now')).toBeTruthy()
    expect(within(rail).getByText('Review extracted signals')).toBeTruthy()
    expect(within(rail).getByText('Durable student record')).toBeTruthy()
    expect(within(rail).getByText('Goals, fit, constraints')).toBeTruthy()
    expect(within(rail).getByText('Shortlist and search memory')).toBeTruthy()
    expect(within(rail).getByText('Prep, applications, decisions')).toBeTruthy()
    expect(within(rail).getByRole('link', { name: 'Workspace: Prep, applications, decisions' })).toBeTruthy()
  })
})
