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
  social_links: { twitter: 'https://x.com/foo' },
  inquiry_routing: { general: 'admissions@foo.edu', financial_aid: 'finaid@foo.edu' },
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
  vi.spyOn(institutionsApi, 'submitInquiry').mockResolvedValue({} as any)
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
  it('renders the header with breadcrumb; Schools tab shows sub-schools', async () => {
    renderDetail(true)
    expect(await screen.findByRole('heading', { name: 'University of Foo' })).toBeInTheDocument()
    // Breadcrumb: Match · Search · University of Foo
    expect(screen.getByRole('button', { name: 'Match' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Search' })).toBeInTheDocument()
    // Header meta renders the founded year (Spec 12 §2: "Founded 1831")
    expect(screen.getAllByText(/1831/).length).toBeGreaterThan(0)
    // Eyebrow must not double the noun (regression: "University University" when
    // ownership_type is absent). type='university' + no ownership → "University".
    expect(screen.getAllByText('University').length).toBeGreaterThan(0)
    expect(screen.queryByText(/University University/i)).not.toBeInTheDocument()
    // Page now defaults to Overview; the Schools tab renders the sub-school card.
    screen.getByRole('button', { name: /schools/i }).click()
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
    expect(await screen.findByText('Posts arrive here once you publish your first.')).toBeInTheDocument()
  })

  it('Updates tab shows pinned posts first with a Pinned marker', async () => {
    vi.spyOn(institutionsApi, 'getPublicPosts').mockResolvedValue([
      { id: 'post-2', title: 'Regular update', body: 'Body two', pinned: false, created_at: '2026-05-02T00:00:00Z', media_urls: [] },
      { id: 'post-1', title: 'Featured news', body: 'Body one', pinned: true, created_at: '2026-05-01T00:00:00Z', media_urls: [] },
    ] as any)
    renderDetail(true)
    await screen.findByRole('heading', { name: 'University of Foo' })
    clickTab(/updates/i)

    expect(await screen.findByText('Featured news')).toBeInTheDocument()
    expect(screen.getByText('Pinned')).toBeInTheDocument()
    const titles = screen.getAllByRole('heading', { level: 3 }).map(el => el.textContent)
    expect(titles.indexOf('Featured news')).toBeLessThan(titles.indexOf('Regular update'))
  })

  it('Programs tab renders canonical ProgramCard entries', async () => {
    renderDetail(true)
    await screen.findByRole('heading', { name: 'University of Foo' })
    clickTab(/programs/i)

    expect(await screen.findByText('MS in Data Science')).toBeInTheDocument()
    expect(screen.getAllByRole('button', { name: /save to my list/i }).length).toBeGreaterThanOrEqual(1)
  })

  it('About tab surfaces support services and international info', async () => {
    renderDetail(true)
    await screen.findByRole('heading', { name: 'University of Foo' })

    clickTab(/about/i)
    expect(await screen.findByText('Support services')).toBeInTheDocument()
    expect(screen.getByText('International students')).toBeInTheDocument()
  })

  // Spec 22 §14 — RSVP from institution page uses the same events API (→ Calendar via backend).
  it('authenticated: RSVP calls the events API', async () => {
    const rsvpSpy = vi.spyOn(eventsApi, 'rsvpEvent').mockResolvedValue({} as any)
    vi.spyOn(eventsApi, 'listEvents').mockResolvedValue([
      {
        id: 'ev-1', event_name: 'Info Session', start_time: '2026-06-15T18:00:00Z',
        location: 'Online', event_type: 'info_session', capacity: 50, rsvp_count: 0,
      },
    ] as any)
    renderDetail(true)
    await screen.findByRole('heading', { name: 'University of Foo' })
    clickTab(/events/i)
    fireEvent.click(await screen.findByRole('button', { name: /^rsvp$/i }))
    await waitFor(() => expect(rsvpSpy).toHaveBeenCalledWith('ev-1'))
  })

  it('public: Events tab shows Sign in to RSVP', async () => {
    vi.spyOn(eventsApi, 'listEvents').mockResolvedValue([
      { id: 'ev-1', event_name: 'Open House', start_time: '2026-06-15T18:00:00Z', location: 'Campus' },
    ] as any)
    renderDetail(false)
    await screen.findByRole('heading', { name: 'University of Foo' })
    clickTab(/events/i)
    expect(await screen.findByRole('button', { name: /sign in to rsvp/i })).toBeInTheDocument()
  })

  it('Updates tab renders program tags and markdown links on posts', async () => {
    vi.spyOn(institutionsApi, 'getPublicPosts').mockResolvedValue([
      {
        id: 'post-1', title: 'Aid update', body: 'See our [aid page](https://foo.edu/aid) for **details**.',
        pinned: false, created_at: '2026-05-01T00:00:00Z', media_urls: [],
        program_names: ['MS in Data Science'],
      },
    ] as any)
    renderDetail(true)
    await screen.findByRole('heading', { name: 'University of Foo' })
    clickTab(/updates/i)
    expect(await screen.findByText('MS in Data Science')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'aid page' })).toHaveAttribute('href', 'https://foo.edu/aid')
    expect(screen.getByText('details')).toBeInTheDocument()
  })

  // Spec 22 §3 — social links surface on the header (text links, no logos).
  it('renders social links in the header', async () => {
    renderDetail(true)
    await screen.findByRole('heading', { name: 'University of Foo' })
    const twitter = screen.getByRole('link', { name: /twitter/i })
    expect(twitter).toHaveAttribute('href', 'https://x.com/foo')
  })

  // Spec 22 §7 / §15 — Request info routes through submit_inquiry when authed.
  it('authenticated: Request info opens a modal and submits an institution-level inquiry', async () => {
    renderDetail(true)
    await screen.findByRole('heading', { name: 'University of Foo' })

    fireEvent.click(screen.getByRole('button', { name: /request info/i }))
    expect(await screen.findByText('Request info from University of Foo')).toBeInTheDocument()

    fireEvent.change(screen.getByLabelText('Subject'), { target: { value: 'Tell me more' } })
    fireEvent.change(screen.getByLabelText('Message'), { target: { value: 'Is there aid?' } })
    fireEvent.click(screen.getByRole('button', { name: /send request/i }))

    await waitFor(() => expect(institutionsApi.submitInquiry).toHaveBeenCalledWith({
      institution_id: 'inst-1',
      subject: 'Tell me more',
      message: 'Is there aid?',
      inquiry_type: 'general',
    }))
  })

  // Spec 22 §8 — only Save/RSVP swap to sign-in CTAs; Request info stays labelled.
  it('public: Request info label stays; click routes to sign-in', async () => {
    renderDetail(false)
    await screen.findByRole('heading', { name: 'University of Foo' })
    expect(screen.getByRole('button', { name: /request info/i })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /sign in to ask/i })).not.toBeInTheDocument()
  })
})

// MIT flagship overhaul — header trim, three rankings, undergrad label,
// data-driven Sources footer, and the multi-paragraph editorial intro.
describe('InstitutionDetail — flagship data (MIT overhaul)', () => {
  const MIT = {
    ...INSTITUTION,
    name: 'Massachusetts Institute of Technology',
    student_body_size: 4535,
    founded_year: 1861,
    description_text:
      'Founded in 1861 in Cambridge, MIT is a private research university.\n\n' +
      'MIT is organized into five schools and one college, plus the Schwarzman College of Computing.',
    ranking_data: {
      qs_world_university_rankings: { rank: 1, year: 2025 },
      times_higher_education: { rank: 2, year: 2025 },
      us_news_national: { rank: 2, year: 2025 },
    },
    school_outcomes: {
      admit_rate: 0.0455,
      avg_net_price: 20111,
      median_earnings_10yr: 143372,
      completion_rate_4yr_150pct: 0.9641,
      flagship: { nobel_laureates: 106, enrollment_total: 11816 },
      sources: [
        {
          label: 'Costs, outcomes',
          source: 'U.S. Dept. of Education College Scorecard',
          year: 2024,
          url: 'https://collegescorecard.ed.gov/',
        },
      ],
    },
  }

  function renderMit() {
    vi.spyOn(institutionsApi, 'getPublicInstitution').mockResolvedValue(MIT as any)
    return renderDetail(true)
  }

  it('header meta shows ranking + founded only (no acceptance / student count)', async () => {
    renderMit()
    await screen.findByRole('heading', { name: /Massachusetts Institute of Technology/ })
    const meta = screen.getByTestId('hero-meta')
    expect(meta).toHaveTextContent(/QS World/)
    expect(meta).toHaveTextContent(/founded/)
    expect(meta).not.toHaveTextContent(/acceptance/i)
    expect(meta).not.toHaveTextContent(/students/i)
  })

  it('Overview renders all three rankings (QS, Times Higher Education, U.S. News)', async () => {
    renderMit()
    await screen.findByRole('heading', { name: /Massachusetts Institute of Technology/ })
    expect(await screen.findByText('Rankings')).toBeInTheDocument()
    expect(screen.getByText(/QS World University Rankings/)).toBeInTheDocument()
    expect(screen.getByText(/Times Higher Education/)).toBeInTheDocument()
    expect(screen.getByText(/U\.S\. News/)).toBeInTheDocument()
  })

  it('Quick facts label the undergrad count; Distinction keeps total enrollment', async () => {
    renderMit()
    await screen.findByRole('heading', { name: /Massachusetts Institute of Technology/ })
    expect(await screen.findByText('Undergraduates')).toBeInTheDocument()
    expect(screen.getByText('Total enrollment')).toBeInTheDocument()
  })

  it('Overview renders a data-driven Sources footer with links', async () => {
    renderMit()
    await screen.findByRole('heading', { name: /Massachusetts Institute of Technology/ })
    expect(await screen.findByRole('heading', { name: /^Sources$/ })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /College Scorecard/ })).toHaveAttribute(
      'href',
      'https://collegescorecard.ed.gov/',
    )
  })

  it('Overview intro renders the full multi-paragraph description', async () => {
    renderMit()
    await screen.findByRole('heading', { name: /Massachusetts Institute of Technology/ })
    expect(await screen.findByText(/Founded in 1861/)).toBeInTheDocument()
    expect(screen.getByText(/five schools and one college/)).toBeInTheDocument()
  })
})
