import { beforeEach, describe, expect, it, vi } from 'vitest'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

vi.mock('../api/my-space', () => ({
  getMySpaceOverview: vi.fn(),
  patchMySpaceTask: vi.fn(),
}))

vi.mock('../lib/analytics', () => ({ track: vi.fn() }))

import { getMySpaceOverview, patchMySpaceTask, type MySpaceOverview } from '../api/my-space'
import { track } from '../lib/analytics'
import MySpaceHomePage from '../pages/student/myspace/MySpaceHomePage'

const overview: MySpaceOverview = {
  generated_at: '2026-06-20T12:00:00Z',
  student: { id: 'student-1', first_name: 'Ada', display_name: 'Ada Lovelace' },
  readiness: [
    {
      key: 'profile',
      label: 'Profile readiness',
      status: 'needs_attention',
      pct: 62,
      detail: '62% of profile signals are present.',
      route: '/s/profile',
      provenance: [{ source: 'adaptive_intake', label: 'Profile signal coverage', href: '/s/profile', confidence: 85, updated_at: null }],
    },
    {
      key: 'match',
      label: 'Match-ready',
      status: 'blocked',
      pct: 62,
      detail: '2 required matching signals still need attention.',
      route: '/s/explore',
      provenance: [{ source: 'adaptive_intake', label: 'Match-ready gate', href: null, confidence: 90, updated_at: null }],
    },
  ],
  tasks: [
    {
      key: 'application:app-1:missing',
      title: 'Complete MS Computer Science application',
      description: 'Missing: Transcript, Statement of purpose',
      owner: 'student',
      urgency: 'focus_now',
      category: 'application',
      cta_label: 'Open application',
      cta_route: '/s/applications/app-1',
      blocker: 'Missing application item',
      missing_field: 'Transcript',
      due_at: '2026-06-22T12:00:00Z',
      provenance: [{ source: 'applications', label: 'Application readiness', href: '/s/applications/app-1', confidence: 80, updated_at: null }],
      dismissed: false,
      snoozed_until: null,
      active: true,
      dismissible: true,
    },
  ],
  pipeline: [
    { key: 'saved', label: 'Saved', value: 2, route: '/s/saved', status: null },
    { key: 'drafts', label: 'In progress', value: 1, route: '/s/applications?status=in_progress', status: null },
    { key: 'submitted', label: 'Submitted', value: 0, route: '/s/applications?status=submitted', status: null },
    { key: 'offers', label: 'Offers', value: 1, route: '/s/applications?tab=offers', status: 'ready' },
  ],
  evidence_gaps: [],
  deadlines: [
    {
      key: 'deadline:1',
      title: 'Submit application',
      description: 'MS Computer Science',
      route: '/s/calendar',
      owner: 'student',
      urgency: 'priority_window',
      status: 'scheduled',
      due_at: '2026-06-25T12:00:00Z',
      provenance: [{ source: 'calendar', label: 'submission_deadline', href: '/s/calendar', confidence: 95, updated_at: null }],
    },
  ],
  waiting_on: [],
  messages: [],
  feedback: [],
  strategy: {
    key: 'strategy:s1',
    title: 'AI product leader',
    description: 'Target MS CS programs with product and AI depth.',
    route: '/s/profile?tab=strategy',
    owner: 'student',
    urgency: 'neutral',
    status: 'active',
    due_at: '2026-06-20T12:00:00Z',
    provenance: [{ source: 'strategy', label: 'Active strategy', href: null, confidence: 85, updated_at: null }],
  },
  prep_readiness: [
    {
      key: 'prep',
      label: 'Prep readiness',
      status: 'needs_attention',
      pct: 25,
      detail: '1/4 prep lanes have usable evidence.',
      route: '/s/prep',
      provenance: [{ source: 'prep', label: 'Workshops, documents, recommenders', href: null, confidence: 80, updated_at: null }],
    },
  ],
  offers: [
    {
      key: 'offer:o1',
      title: 'MS Computer Science',
      description: 'Offer needs comparison before response.',
      route: '/s/applications?tab=offers',
      owner: 'student',
      urgency: 'priority_window',
      status: 'extended',
      due_at: '2026-07-01T12:00:00Z',
      provenance: [{ source: 'offer_letters', label: 'Offer letter', href: null, confidence: 90, updated_at: null }],
    },
  ],
  saved_targets: [],
  import_status: {
    key: 'import:status',
    title: 'No materials imported',
    description: 'Upload a transcript, resume, essay draft, or offer letter to reduce manual entry.',
    route: '/s/import',
    owner: 'student',
    urgency: 'gentle_attention',
    status: 'empty',
    due_at: null,
    provenance: [{ source: 'documents', label: 'No uploaded materials', href: null, confidence: 90, updated_at: null }],
  },
  recent_changes: [],
  access_issues: [],
}

beforeEach(() => {
  vi.mocked(getMySpaceOverview).mockResolvedValue(overview)
  vi.mocked(patchMySpaceTask).mockResolvedValue({
    task_key: 'application:app-1:missing',
    dismissed: true,
    snoozed_until: null,
  })
  vi.mocked(track).mockClear()
})

function renderHome() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <MySpaceHomePage />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('MySpaceHomePage', () => {
  it('renders the server-composed command center modules', async () => {
    renderHome()

    expect(await screen.findByText(/Good (morning|afternoon|evening), Ada/)).toBeTruthy()
    expect(screen.getByText('Complete MS Computer Science application')).toBeTruthy()
    expect(screen.getByText('Readiness ledger')).toBeTruthy()
    expect(screen.getByText('Evidence gaps')).toBeTruthy()
    expect(screen.getByText('Offers & costs')).toBeTruthy()
    expect(screen.getByText('Import & clarification')).toBeTruthy()
    expect(screen.getByText('Application readiness · applications · 80% confidence')).toBeTruthy()
  })

  it('persists dismiss state for computed tasks', async () => {
    renderHome()

    const dismiss = await screen.findAllByText('Dismiss')
    fireEvent.click(dismiss[0])

    await waitFor(() => {
      expect(patchMySpaceTask).toHaveBeenCalledWith('application:app-1:missing', { dismissed: true })
    })
  })
})
