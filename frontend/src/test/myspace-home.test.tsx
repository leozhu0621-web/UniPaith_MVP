import { beforeEach, describe, expect, it, vi } from 'vitest'
import { fireEvent, render, screen, waitFor, within } from '@testing-library/react'
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
  application_portfolio: [
    {
      key: 'application:app-1',
      title: 'MS Data Science application',
      description: 'Missing Transcript, Statement of purpose. 55% ready.',
      route: '/s/applications/app-1',
      owner: 'student',
      urgency: 'priority_window',
      status: 'in_progress',
      due_at: '2026-06-27T23:59:00Z',
      provenance: [{ source: 'applications', label: 'in_progress', href: '/s/applications/app-1', confidence: 85, updated_at: null }],
    },
  ],
  messages: [
    {
      key: 'message:thread-1',
      title: 'Admissions follow-up',
      description: 'Admissions office asked for an updated transcript.',
      route: '/s/messages?thread=thread-1',
      owner: 'student',
      urgency: 'priority_window',
      status: 'unread',
      due_at: '2026-06-23T12:00:00Z',
      provenance: [{ source: 'messages', label: 'unread', href: '/s/messages?thread=thread-1', confidence: 85, updated_at: null }],
    },
  ],
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
  vi.mocked(getMySpaceOverview).mockClear()
  vi.mocked(patchMySpaceTask).mockClear()
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
    expect(screen.getByText(/Updated .*1 active task.*0 hidden tasks/)).toBeTruthy()
    expect(screen.getByText('source-backed')).toBeTruthy()
    expect(screen.getByText('Complete MS Computer Science application')).toBeTruthy()
    expect(screen.getByText('Readiness ledger')).toBeTruthy()
    expect(screen.getByText('Application portfolio')).toBeTruthy()
    expect(screen.getByText('MS Data Science application')).toBeTruthy()
    expect(screen.getByText('Evidence gaps')).toBeTruthy()
    expect(screen.getByText('Messages')).toBeTruthy()
    expect(screen.getByText('Admissions follow-up')).toBeTruthy()
    expect(screen.getByText('Offers & costs')).toBeTruthy()
    expect(screen.getByText('Import & clarification')).toBeTruthy()
    expect(screen.getAllByText('Application readiness · applications · 80% confidence').length).toBeGreaterThan(0)
  })

  it('routes application portfolio rows to the owning application', async () => {
    renderHome()

    fireEvent.click(await screen.findByText('MS Data Science application'))

    expect(track).toHaveBeenCalledWith('my_space_task_clicked', {
      route: '/s/applications/app-1',
      module: 'application_portfolio',
      key: 'application:app-1',
    })
  })

  it('persists dismiss state for computed tasks', async () => {
    renderHome()

    fireEvent.click(await screen.findByLabelText('Dismiss Complete MS Computer Science application'))

    await waitFor(() => {
      expect(patchMySpaceTask).toHaveBeenCalledWith('application:app-1:missing', { dismissed: true })
    })
  })

  it('lets students restore dismissed or snoozed tasks from the hidden task panel', async () => {
    vi.mocked(getMySpaceOverview).mockResolvedValueOnce({
      ...overview,
      tasks: [
        {
          ...overview.tasks[0],
          dismissed: true,
          active: false,
        },
      ],
      evidence_gaps: [],
    })

    renderHome()
    fireEvent.click(await screen.findByText('Hidden tasks'))
    fireEvent.click(await screen.findByLabelText('Restore Complete MS Computer Science application'))

    expect(track).toHaveBeenCalledWith('my_space_task_restored', {
      task_key: 'application:app-1:missing',
      category: 'application',
    })
    await waitFor(() => {
      expect(patchMySpaceTask).toHaveBeenCalledWith('application:app-1:missing', {
        dismissed: false,
        snoozed_until: null,
      })
    })
  })

  it('surfaces recommender risk nudges in waiting on others', async () => {
    vi.mocked(getMySpaceOverview).mockResolvedValueOnce({
      ...overview,
      waiting_on: [
        {
          key: 'recommender:r1',
          title: 'Prof. Lee recommendation',
          description: 'Letter is due soon. Nudge the recommender or confirm a backup.',
          route: '/s/prep?tab=recommenders',
          owner: 'recommender',
          urgency: 'focus_now',
          status: 'due_soon',
          due_at: '2026-06-22T23:59:00Z',
          provenance: [{ source: 'recommendation_requests', label: 'due_soon', href: null, confidence: 90, updated_at: null }],
        },
      ],
    })

    renderHome()

    expect(await screen.findByText('Prof. Lee recommendation')).toBeTruthy()
    expect(screen.getByText('Letter is due soon. Nudge the recommender or confirm a backup.')).toBeTruthy()
    expect(screen.getByText('due soon')).toBeTruthy()

    fireEvent.click(screen.getByText('Prof. Lee recommendation'))
    expect(track).toHaveBeenCalledWith('recommender_nudge_clicked', {
      route: '/s/prep?tab=recommenders',
      module: 'waiting_on',
      key: 'recommender:r1',
    })
  })

  it('surfaces admissions messages and routes to the owning thread', async () => {
    renderHome()

    expect(await screen.findByText('Admissions follow-up')).toBeTruthy()
    expect(screen.getByText('Admissions office asked for an updated transcript.')).toBeTruthy()
    expect(screen.getByText('unread')).toBeTruthy()

    fireEvent.click(screen.getByText('Admissions follow-up'))
    expect(track).toHaveBeenCalledWith('my_space_task_clicked', {
      route: '/s/messages?thread=thread-1',
      module: 'messages',
      key: 'message:thread-1',
    })
  })

  it('shows blocker and missing-field context on module task rows', async () => {
    vi.mocked(getMySpaceOverview).mockResolvedValueOnce({
      ...overview,
      evidence_gaps: [
        {
          key: 'clarification:gpa',
          title: 'Confirm GPA',
          description: 'Uni needs this before trusting the signal.',
          owner: 'student',
          urgency: 'priority_window',
          category: 'clarification',
          cta_label: 'Clarify in Uni',
          cta_route: '/s?intent=clarification&source_task=clarification%3Agpa&return_to=%2Fs%2Fspace&artifact_destination=clarification',
          blocker: 'Low-confidence extracted signal',
          missing_field: 'GPA',
          due_at: null,
          provenance: [{ source: 'adaptive_intake', label: 'Clarification', href: '/s/import', confidence: 55, updated_at: null }],
          dismissed: false,
          snoozed_until: null,
          active: true,
          dismissible: true,
        },
      ],
    })

    renderHome()

    expect(await screen.findByText('Confirm GPA')).toBeTruthy()
    expect(screen.getByText('Low-confidence extracted signal · GPA')).toBeTruthy()
    expect(screen.getAllByText(/Clarification .* adaptive intake .* 55% confidence/).length).toBeGreaterThan(0)
  })

  it('lets students inspect provenance and review the source record', async () => {
    vi.mocked(getMySpaceOverview).mockResolvedValueOnce({
      ...overview,
      evidence_gaps: [
        {
          key: 'clarification:gpa',
          title: 'Confirm GPA',
          description: 'Uni needs this before trusting the signal.',
          owner: 'student',
          urgency: 'priority_window',
          category: 'clarification',
          cta_label: 'Clarify in Uni',
          cta_route: '/s?intent=clarification&source_task=clarification%3Agpa&return_to=%2Fs%2Fspace&artifact_destination=clarification',
          blocker: 'Low-confidence extracted signal',
          missing_field: 'GPA',
          due_at: null,
          provenance: [{ source: 'adaptive_intake', label: 'Clarification', href: '/s/import', confidence: 55, updated_at: null }],
          dismissed: false,
          snoozed_until: null,
          active: true,
          dismissible: true,
        },
      ],
    })

    renderHome()

    const title = await screen.findByText('Confirm GPA')
    const row = title.closest('[data-task-key="clarification:gpa"]')
    expect(row).toBeTruthy()

    fireEvent.click(within(row as HTMLElement).getByText('Why this appears'))
    fireEvent.click(within(row as HTMLElement).getByRole('button', { name: 'Review source' }))

    expect(track).toHaveBeenCalledWith('readiness_explanation_opened', {
      route: '/s/import',
      task_key: 'clarification:gpa',
      category: 'clarification',
      source: 'provenance',
    })
  })

  it('lets students inspect readiness provenance and review the source record', async () => {
    renderHome()

    const title = await screen.findByText('Profile readiness')
    const row = title.closest('[data-readiness-key="profile"]')
    expect(row).toBeTruthy()

    fireEvent.click(within(row as HTMLElement).getByText('Why this appears'))
    fireEvent.click(within(row as HTMLElement).getByRole('button', { name: 'Review source' }))

    expect(track).toHaveBeenCalledWith('readiness_explanation_opened', {
      route: '/s/profile',
      key: 'profile',
      status: 'needs_attention',
      source: 'provenance',
    })
  })

  it('shows all partial dependency access issues', async () => {
    vi.mocked(getMySpaceOverview).mockResolvedValueOnce({
      ...overview,
      access_issues: [
        { source: 'applications', label: 'Applications temporarily unavailable', href: null, confidence: null, updated_at: null },
        { source: 'messages', label: 'Messages temporarily unavailable', href: null, confidence: null, updated_at: null },
      ],
    })

    renderHome()

    expect(await screen.findByText('2 My Space data sources are using fallback data.')).toBeTruthy()
    fireEvent.click(screen.getByText('View affected sources'))
    expect(screen.getByText('Applications temporarily unavailable · applications')).toBeTruthy()
    expect(screen.getByText('Messages temporarily unavailable · messages')).toBeTruthy()
  })

  it('surfaces offer decision pressure in offers and costs', async () => {
    vi.mocked(getMySpaceOverview).mockResolvedValueOnce({
      ...overview,
      offers: [
        {
          key: 'offer:o1',
          title: 'MS Data Science offer',
          description: 'Offer response is due soon. Compare cost, conditions, and fit now. Aid: $12,000.',
          route: '/s/applications?tab=offers',
          owner: 'student',
          urgency: 'focus_now',
          status: 'due_soon',
          due_at: '2026-06-22T23:59:00Z',
          provenance: [{ source: 'offer_letters', label: 'due_soon', href: null, confidence: 90, updated_at: null }],
        },
      ],
    })

    renderHome()

    expect(await screen.findByText('MS Data Science offer')).toBeTruthy()
    expect(screen.getByText('Offer response is due soon. Compare cost, conditions, and fit now. Aid: $12,000.')).toBeTruthy()
    expect(screen.getByText('due soon')).toBeTruthy()

    fireEvent.click(screen.getByText('MS Data Science offer'))
    expect(track).toHaveBeenCalledWith('offer_compare_opened', {
      route: '/s/applications?tab=offers',
      key: 'offer:o1',
    })
  })

  it('tracks Uni handoffs with decoded contract fields', async () => {
    vi.mocked(getMySpaceOverview).mockResolvedValueOnce({
      ...overview,
      tasks: [
        {
          key: 'strategy:create',
          title: 'Create your admissions strategy',
          description: 'Turn profile signals into a career, degree, academic, financial, and geographic plan.',
          owner: 'student',
          urgency: 'gentle_attention',
          category: 'strategy',
          cta_label: 'Draft with Uni',
          cta_route: '/s?intent=strategy&source_task=strategy%3Acreate&return_to=%2Fs%2Fspace&artifact_destination=strategy_draft',
          blocker: 'No active strategy',
          missing_field: null,
          due_at: null,
          provenance: [{ source: 'strategy', label: 'No active living document', href: null, confidence: 80, updated_at: null }],
          dismissed: false,
          snoozed_until: null,
          active: true,
          dismissible: true,
        },
      ],
      strategy: null,
    })

    renderHome()
    fireEvent.click(await screen.findByLabelText('Draft with Uni: Create your admissions strategy'))

    expect(track).toHaveBeenCalledWith('uni_chat_handoff_started', {
      route: '/s?intent=strategy&source_task=strategy%3Acreate&return_to=%2Fs%2Fspace&artifact_destination=strategy_draft',
      intent: 'strategy',
      source_task: 'strategy:create',
      return_to: '/s/space',
      artifact_destination: 'strategy_draft',
    })
  })
})
