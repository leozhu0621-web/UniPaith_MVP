// My Space rail restructure (Spec 2026-06-14) — rooms grouped by content type
// (Record / Collections / Workspace), not application-journey phase.
import { describe, it, expect, vi } from 'vitest'
import { render, screen, within } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

vi.mock('../components/ui/Coachmark', () => ({ default: ({ children }: { children: React.ReactNode }) => children }))
vi.mock('../api/inbox', () => ({ getThreads: vi.fn(() => Promise.resolve([])) }))
vi.mock('../api/applications', () => ({ listMyApplications: vi.fn(() => Promise.resolve([])) }))

import MySpaceShell, { MY_SPACE_ROUTES } from '../pages/student/myspace/MySpaceShell'

function renderShell(initialPath = '/s/space') {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter initialEntries={[initialPath]}>
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
      .map(a => (a.textContent ?? '').trim())
    // At /s/space no group is expanded, so the only links are the two top-level
    // items — Import sits right after Overview (Spec 2026-06-16).
    expect(links.slice(0, 2)).toEqual(['Overview', 'Import'])
  })

  it('points Import at /s/import', () => {
    renderShell()
    const rail = screen.getByRole('complementary', { name: 'My Space' })
    expect(
      within(rail).getByRole('link', { name: /^Import/ }).getAttribute('href'),
    ).toBe('/s/import')
  })
})

describe('MY_SPACE_ROUTES (derived from the rail tree)', () => {
  it('includes /s/import (the bug this derivation fixes)', () => {
    expect(MY_SPACE_ROUTES).toContain('/s/import')
  })

  it('includes every distinct room pathname in the tree', () => {
    // Roots + group children, query strings stripped. Order doesn't matter
    // (isMySpacePath uses .some), so compare as sets.
    const expected = [
      '/s/space', '/s/import', '/s/profile', '/s/saved', '/s/prep',
      '/s/applications', '/s/calendar',
    ]
    expect(new Set(MY_SPACE_ROUTES)).toEqual(new Set(expected))
  })

  it('keeps the pathnames distinct (Profile/Planning share /s/profile)', () => {
    expect(MY_SPACE_ROUTES.length).toBe(new Set(MY_SPACE_ROUTES).size)
    // /s/profile appears once even though both Profile and Planning use it.
    expect(MY_SPACE_ROUTES.filter(p => p === '/s/profile')).toHaveLength(1)
  })

  it('omits /s/messages (its own nav tab, not in the tree)', () => {
    expect(MY_SPACE_ROUTES).not.toContain('/s/messages')
  })
})

describe('landing rail rows highlight on their page default tab', () => {
  const activeClass = 'font-medium'

  it('renders the rail at /s/import without crashing and highlights Import', () => {
    renderShell('/s/import')
    const rail = screen.getByRole('complementary', { name: 'My Space' })
    const importLink = within(rail).getByRole('link', { name: /^Import/ })
    const overviewLink = within(rail).getByRole('link', { name: /^Overview/ })
    expect(importLink.className).toContain(activeClass)
    expect(overviewLink.className).not.toContain(activeClass)
  })

  it('highlights Overview on /s/space (bare path, no tab)', () => {
    renderShell('/s/space')
    const rail = screen.getByRole('complementary', { name: 'My Space' })
    expect(within(rail).getByRole('link', { name: /^Overview/ }).className).toContain(activeClass)
  })

  it('highlights "Programs" on /s/saved (Saved default tab)', () => {
    renderShell('/s/saved')
    const rail = screen.getByRole('complementary', { name: 'My Space' })
    expect(within(rail).getByRole('link', { name: 'Programs' }).className).toContain(activeClass)
  })

  it('highlights "Workshops" on /s/prep (Workspace default tab)', () => {
    renderShell('/s/prep')
    const rail = screen.getByRole('complementary', { name: 'My Space' })
    expect(within(rail).getByRole('link', { name: 'Workshops' }).className).toContain(activeClass)
  })

  it('highlights "Basic info" on /s/profile (Profile default tab)', () => {
    renderShell('/s/profile')
    const rail = screen.getByRole('complementary', { name: 'My Space' })
    expect(within(rail).getByRole('link', { name: 'Basic info' }).className).toContain(activeClass)
  })
})
