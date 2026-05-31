import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter } from 'react-router-dom'
import InstitutionDetail from '../pages/student/institution/InstitutionDetail'
import * as institutionsApi from '../api/institutions'
import * as programsApi from '../api/programs'
import * as eventsApi from '../api/events'
import * as savedApi from '../api/saved-lists'

// Spec 12 — School Detail page. Covers the spec §11 test checklist:
// tab routing + default tab, authenticated-vs-public action differences,
// the Programs tab Discovery-style chip/filter behavior, and the breadcrumb.

const INSTITUTION = {
  id: 'inst-1', name: 'University of Foo', type: 'university',
  country: 'USA', city: 'New York', region: 'NY',
  campus_setting: 'urban', student_body_size: 51000, founded_year: 1831,
  support_services: { tutoring: { name: 'Tutoring' } },
  international_info: { supported_visas: ['F-1'] },
  school_outcomes: { employed_or_continuing_ed: 0.94 },
}

const SCHOOLS = [
  { id: 'sch-1', institution_id: 'inst-1', name: 'School of Engineering', description_text: 'Eng', program_count: 2, program_names: [] },
]

const PROGRAMS = [
  { id: 'p1', institution_id: 'inst-1', program_name: 'MS in Data Science', degree_type: 'masters', department: 'CS', delivery_format: 'in_person', tuition: 50000, duration_months: 12, acceptance_rate: 0.1, application_deadline: null, institution_name: 'University of Foo', institution_country: 'USA', institution_city: 'New York', median_salary: null, employment_rate: null, payback_months: null },
  { id: 'p2', institution_id: 'inst-1', program_name: 'PhD in Physics', degree_type: 'phd', department: 'Physics', delivery_format: 'in_person', tuition: 0, duration_months: 60, acceptance_rate: 0.05, application_deadline: null, institution_name: 'University of Foo', institution_country: 'USA', institution_city: 'New York', median_salary: null, employment_rate: null, payback_months: null },
]

/** Click a tab by its visible label (robust to the count suffix in the label). */
function clickTab(label: RegExp) {
  const tab = screen.getAllByRole('tab').find(el => label.test(el.textContent ?? ''))
  if (!tab) throw new Error(`Tab matching ${label} not found`)
  fireEvent.click(tab)
}

function mockApis() {
  vi.spyOn(institutionsApi, 'getPublicInstitution').mockResolvedValue(INSTITUTION as any)
  vi.spyOn(institutionsApi, 'getInstitutionSchools').mockResolvedValue(SCHOOLS as any)
  vi.spyOn(institutionsApi, 'getPublicPosts').mockResolvedValue([] as any)
  vi.spyOn(programsApi, 'searchPrograms').mockResolvedValue({ items: PROGRAMS, total: 2, page: 1, page_size: 100, total_pages: 1 } as any)
  vi.spyOn(eventsApi, 'listEvents').mockResolvedValue([] as any)
  vi.spyOn(eventsApi, 'getMyRsvps').mockResolvedValue([] as any)
  vi.spyOn(eventsApi, 'getMyFollows').mockResolvedValue([] as any)
  vi.spyOn(savedApi, 'listSaved').mockResolvedValue([] as any)
}

function renderDetail(isAuthenticated = true) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter initialEntries={['/s/institutions/inst-1']}>
        <InstitutionDetail institutionId="inst-1" isAuthenticated={isAuthenticated} />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

beforeEach(() => {
  vi.restoreAllMocks()
  mockApis()
})

describe('InstitutionDetail (Spec 12)', () => {
  it('renders the header with breadcrumb and defaults to the Schools tab', async () => {
    renderDetail(true)
    expect(await screen.findByRole('heading', { name: 'University of Foo' })).toBeInTheDocument()
    // Breadcrumb: Match · Search · University of Foo
    expect(screen.getByRole('button', { name: 'Match' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Search' })).toBeInTheDocument()
    // Default tab = Schools → the sub-school card shows
    await waitFor(() => expect(screen.getByText('School of Engineering')).toBeInTheDocument())
  })

  it('authenticated surface shows "Save school"; public shows "Sign in to save"', async () => {
    const { unmount } = renderDetail(true)
    expect(await screen.findByRole('button', { name: /save school/i })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /sign in to save/i })).not.toBeInTheDocument()
    unmount()

    mockApis()
    renderDetail(false)
    expect(await screen.findByRole('button', { name: /sign in to save/i })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /save school/i })).not.toBeInTheDocument()
  })

  it('Programs tab shows the locked scope chip and filters by search', async () => {
    renderDetail(true)
    await screen.findByRole('heading', { name: 'University of Foo' })

    clickTab(/programs/i)

    // Locked scope chip (Spec 12 §3.4)
    expect(await screen.findByText('Institution · University of Foo')).toBeInTheDocument()
    expect(screen.getByText('MS in Data Science')).toBeInTheDocument()
    expect(screen.getByText('PhD in Physics')).toBeInTheDocument()

    // Search filter narrows the grid
    fireEvent.change(screen.getByPlaceholderText('Search programs'), { target: { value: 'Physics' } })
    await waitFor(() => {
      expect(screen.queryByText('MS in Data Science')).not.toBeInTheDocument()
      expect(screen.getByText('PhD in Physics')).toBeInTheDocument()
    })
  })

  it('Events and Updates tabs show the spec empty-state copy', async () => {
    renderDetail(true)
    await screen.findByRole('heading', { name: 'University of Foo' })

    clickTab(/events/i)
    expect(await screen.findByText('No events scheduled')).toBeInTheDocument()

    clickTab(/updates/i)
    expect(await screen.findByText('No updates yet')).toBeInTheDocument()
  })

  it('About tab surfaces support services and international info', async () => {
    renderDetail(true)
    await screen.findByRole('heading', { name: 'University of Foo' })

    clickTab(/about/i)
    expect(await screen.findByText('Support services')).toBeInTheDocument()
    expect(screen.getByText('International students')).toBeInTheDocument()
  })
})
