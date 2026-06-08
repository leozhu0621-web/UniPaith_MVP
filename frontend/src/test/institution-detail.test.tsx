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
    // Founded year now lives in Quick facts / About (the header is chip-free).
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
      retention_rate_first_year: 0.9908,
      employed_or_continuing_ed: 0.94,
      top_employer_industries: ['Technology', 'Finance', 'Consulting'],
      financial_aid: {
        pell_grant_rate: 0.1932,
        federal_loan_rate: 0.0669,
        median_debt_completers: 14768,
        cost_of_attendance: 89340,
        tuition_free_rate: 0.39,
        no_loan_debt_rate: 0.88,
        median_scholarship: 69777,
      },
      demographics: { asian: 0.3517, white: 0.2126, hispanic: 0.1409, women: 0.4816 },
      scale: {
        faculty_count: 1466,
        student_faculty_ratio: '3:1',
        research_centers: 70,
        endowment_usd: 24600000000,
        campus_acres: 168,
        undergrad_majors: 56,
      },
      research: { labs: ['CSAIL', 'MIT Media Lab', 'Lincoln Laboratory'], areas: ['AI & computing', 'Fusion energy'], industry_collaborators: 700 },
      campus_life: { varsity_sports: 33, athletics_division: 'NCAA Division III', arts_groups: 60, residence_halls: 20 },
      flagship: {
        nobel_laureates: 106,
        macarthur_fellows: 85,
        national_medal_science: 64,
        national_medal_tech: 35,
        enrollment_total: 11816,
        admissions_cycle: 'Class of 2029',
        applicants: 29281,
        admits: 1334,
      },
      sources: [
        {
          label: 'Costs, outcomes',
          source: 'U.S. Dept. of Education College Scorecard',
          year: 2024,
          url: 'https://collegescorecard.ed.gov/',
        },
        { label: 'World ranking', source: 'QS World University Rankings', year: 2025, url: 'https://www.topuniversities.com/universities/mit' },
        { label: 'World ranking', source: 'Times Higher Education', year: 2025, url: 'https://www.timeshighereducation.com/mit' },
        { label: 'National ranking', source: 'U.S. News Best National Universities', year: 2025, url: 'https://www.usnews.com/best-colleges/mit' },
        { label: 'Facts & profile', source: 'MIT Facts', year: 2025, url: 'https://facts.mit.edu/' },
      ],
    },
  }

  function renderMit() {
    vi.spyOn(institutionsApi, 'getPublicInstitution').mockResolvedValue(MIT as any)
    return renderDetail(true)
  }

  it('header is chip-free — no founded/ranking/acceptance/students meta line; founded lives in Quick facts', async () => {
    renderMit()
    await screen.findByRole('heading', { name: /Massachusetts Institute of Technology/ })
    // The header meta chip line was removed entirely (per design feedback).
    expect(screen.queryByTestId('hero-meta')).not.toBeInTheDocument()
    // Founded still appears — in Quick facts / About, not the header.
    expect(screen.getAllByText(/founded/i).length).toBeGreaterThan(0)
  })

  it('Overview renders all three rankings as badges (QS, THE, U.S. News)', async () => {
    renderMit()
    await screen.findByRole('heading', { name: /Massachusetts Institute of Technology/ })
    expect(await screen.findByText('Rankings')).toBeInTheDocument()
    const badges = screen.getAllByTestId('ranking-badge')
    expect(badges.some(b => /QS World University Rankings/.test(b.textContent ?? ''))).toBe(true)
    expect(badges.some(b => /Times Higher Education/.test(b.textContent ?? ''))).toBe(true)
    expect(badges.some(b => /U\.S\. News/.test(b.textContent ?? ''))).toBe(true)
  })

  it('ranking badges link to their reference source (round 3)', async () => {
    renderMit()
    await screen.findByRole('heading', { name: /Massachusetts Institute of Technology/ })
    const badges = await screen.findAllByTestId('ranking-badge')
    const qs = badges.find(b => /QS World University Rankings/.test(b.textContent ?? ''))
    expect(qs?.tagName).toBe('A')
    expect(qs).toHaveAttribute('href', 'https://www.topuniversities.com/universities/mit')
    expect(qs).toHaveAttribute('target', '_blank')
  })

  it('Diversity section leads with the breakdown + a compact enrollment line (round 3)', async () => {
    renderMit()
    await screen.findByRole('heading', { name: /Massachusetts Institute of Technology/ })
    expect(await screen.findByRole('heading', { name: /Diversity/ })).toBeInTheDocument()
    expect(screen.getByText(/4,535 undergraduate/)).toBeInTheDocument()
    expect(screen.getByText(/11,816 total enrollment/)).toBeInTheDocument()
  })

  it('Admissions renders the funnel (applied → admitted → rate)', async () => {
    renderMit()
    await screen.findByRole('heading', { name: /Massachusetts Institute of Technology/ })
    expect(await screen.findByText('29,281')).toBeInTheDocument()
    expect(screen.getByText('1,334')).toBeInTheDocument()
    expect(screen.getByText('Class of 2029')).toBeInTheDocument()
    expect(screen.getByText('Applied')).toBeInTheDocument()
  })

  it('Cost & aid leads with net price and shows an aid bar', async () => {
    renderMit()
    await screen.findByRole('heading', { name: /Massachusetts Institute of Technology/ })
    expect(await screen.findByText(/Cost & aid/)).toBeInTheDocument()
    expect(screen.getAllByText('$20K').length).toBeGreaterThan(0)
    expect(screen.getByText('Pell grant recipients')).toBeInTheDocument()
  })

  it('Outcomes surfaces top industries as chips', async () => {
    renderMit()
    await screen.findByRole('heading', { name: /Massachusetts Institute of Technology/ })
    expect(await screen.findByText('Top industries')).toBeInTheDocument()
    expect(screen.getByText('Technology')).toBeInTheDocument()
    expect(screen.getByText('Finance')).toBeInTheDocument()
  })

  it('Student body renders a race & ethnicity breakdown', async () => {
    renderMit()
    await screen.findByRole('heading', { name: /Massachusetts Institute of Technology/ })
    expect(await screen.findByText('Race & ethnicity')).toBeInTheDocument()
    expect(screen.getByText('Asian')).toBeInTheDocument()
  })

  it('Overview renders a data-driven Sources footer with links', async () => {
    renderMit()
    await screen.findByRole('heading', { name: /Massachusetts Institute of Technology/ })
    expect(await screen.findByRole('heading', { name: /^Sources$/ })).toBeInTheDocument()
    const scorecard = screen.getAllByRole('link', { name: /College Scorecard/ })
    expect(scorecard.some(l => l.getAttribute('href') === 'https://collegescorecard.ed.gov/')).toBe(true)
  })

  it('Cost & aid shows an inline source citation (round 3)', async () => {
    renderMit()
    await screen.findByRole('heading', { name: /Massachusetts Institute of Technology/ })
    expect(await screen.findByText(/Cost & aid/)).toBeInTheDocument()
    // both the footer and the cost card now cite College Scorecard
    expect(screen.getAllByRole('link', { name: /College Scorecard/ }).length).toBeGreaterThanOrEqual(2)
  })

  it('By the numbers surfaces institutional scale (crawl phase 1)', async () => {
    renderMit()
    await screen.findByRole('heading', { name: /Massachusetts Institute of Technology/ })
    clickTab(/about/i)
    expect(await screen.findByRole('heading', { name: /By the numbers/ })).toBeInTheDocument()
    expect(screen.getByText('Faculty')).toBeInTheDocument()
    expect(screen.getByText('1,466')).toBeInTheDocument()
    expect(screen.getByText('$24.6B')).toBeInTheDocument()
  })

  it('Cost & aid shows the sticker price and aid highlights (crawl phase 1)', async () => {
    renderMit()
    await screen.findByRole('heading', { name: /Massachusetts Institute of Technology/ })
    expect(await screen.findByText(/Sticker cost of attendance/)).toBeInTheDocument()
    expect(screen.getByText('Attend tuition-free')).toBeInTheDocument()
    expect(screen.getByText('Graduate debt-free')).toBeInTheDocument()
  })

  it('Recognition includes the national medals (crawl phase 1)', async () => {
    renderMit()
    await screen.findByRole('heading', { name: /Massachusetts Institute of Technology/ })
    clickTab(/about/i)
    expect(await screen.findByText('National Medal of Science')).toBeInTheDocument()
    expect(screen.getByText('64')).toBeInTheDocument()
  })

  it('Research & innovation lists labs + areas (crawl phase 3)', async () => {
    renderMit()
    await screen.findByRole('heading', { name: /Massachusetts Institute of Technology/ })
    clickTab(/about/i)
    expect(await screen.findByRole('heading', { name: /Research & innovation/ })).toBeInTheDocument()
    expect(screen.getByText('CSAIL')).toBeInTheDocument()
    expect(screen.getByText('MIT Media Lab')).toBeInTheDocument()
  })

  it('Campus life shows athletics + arts (crawl phase 3)', async () => {
    renderMit()
    await screen.findByRole('heading', { name: /Massachusetts Institute of Technology/ })
    clickTab(/about/i)
    expect(await screen.findByRole('heading', { name: /Campus life/ })).toBeInTheDocument()
    expect(screen.getByText(/Varsity sports/)).toBeInTheDocument()
    expect(screen.getByText('Arts groups')).toBeInTheDocument()
  })

  it('Overview intro renders the full multi-paragraph description', async () => {
    renderMit()
    await screen.findByRole('heading', { name: /Massachusetts Institute of Technology/ })
    expect(await screen.findByText(/Founded in 1861/)).toBeInTheDocument()
    expect(screen.getByText(/five schools and one college/)).toBeInTheDocument()
  })

  it('intro carries an inline MIT Facts source citation (phase B)', async () => {
    renderMit()
    await screen.findByRole('heading', { name: /Massachusetts Institute of Technology/ })
    const factsLinks = await screen.findAllByRole('link', { name: /MIT Facts/ })
    expect(factsLinks.length).toBeGreaterThanOrEqual(1)
    expect(factsLinks[0]).toHaveAttribute('href', 'https://facts.mit.edu/')
  })
})
