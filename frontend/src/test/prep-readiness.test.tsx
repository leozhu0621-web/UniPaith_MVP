import type { ReactElement } from 'react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

import type { Interview, RecommendationRequest } from '../types'
import type { PromptLibrarySummary } from '../types/promptLibrary'

vi.mock('../api/prompt-library', () => ({ getSummary: vi.fn() }))
vi.mock('../api/documents', () => ({ listDocuments: vi.fn() }))
vi.mock('../api/interviews', () => ({ getMyInterviews: vi.fn() }))
vi.mock('../api/recommendations', () => ({ listRecommendations: vi.fn() }))

vi.mock('../pages/student/apply/WorkshopsTab', () => ({ default: () => <div>Workshops tab</div> }))
vi.mock('../pages/student/apply/promptlibrary/PromptLibraryTab', () => ({ default: () => <div>Prompt library tab</div> }))
vi.mock('../pages/student/myspace/prep/InterviewsTab', () => ({ default: () => <div>Interviews tab</div> }))
vi.mock('../pages/student/myspace/prep/RecommendersTab', () => ({ default: () => <div>Recommenders tab</div> }))
vi.mock('../pages/student/myspace/prep/DocumentsTab', () => ({ default: () => <div>Documents tab</div> }))

import { getSummary } from '../api/prompt-library'
import { listDocuments } from '../api/documents'
import { getMyInterviews } from '../api/interviews'
import { listRecommendations } from '../api/recommendations'
import PrepPage from '../pages/student/myspace/PrepPage'

const SUMMARY: PromptLibrarySummary = {
  total_prompts: 4,
  answered_count: 1,
  final_count: 0,
  draft_count: 1,
  stories_count: 1,
  inference_enabled: true,
  interview_readiness_band: 'low',
  interview_readiness_score: 25,
  readiness_detail: { band: 'low', score: 25, answered: 1, core_total: 4, star_avg: 1 },
  competency_coverage_map: { leadership: 0 },
  competency_coverage_gaps: ['leadership'],
  story_prompt_matching_table: [],
  revision_priority_list: [],
  suggested_practice_plan: 'Start with leadership evidence.',
}

const INTERVIEW: Interview = {
  id: 'iv-1',
  application_id: 'app-1',
  applicant: { student_id: 'student-1', name: 'Student' },
  program: { id: 'program-1', name: 'MS CS' },
  interviewer_id: null,
  interview_type: 'live',
  status: 'proposed',
  async_expired: false,
  proposed_times: [],
  proposed_slots: null,
  confirmed_time: null,
  scheduled_at: null,
  duration_minutes: 30,
  location: null,
  meeting_link: null,
  location_or_link: null,
  async_window_end: null,
  recording_url: null,
  notes_to_student: null,
  recommendation: null,
  scores: [],
  created_at: null,
}

const RECOMMENDER: RecommendationRequest = {
  id: 'rec-1',
  student_id: 'student-1',
  recommender_name: 'Prof. Lee',
  recommender_email: 'lee@example.edu',
  recommender_title: null,
  recommender_institution: null,
  relationship: 'Professor',
  status: 'draft',
  requested_at: null,
  due_date: new Date(Date.now() + 3 * 24 * 60 * 60 * 1000).toISOString(),
  notes: null,
  target_program_id: null,
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-01T00:00:00Z',
}

function renderPage(ui: ReactElement) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter initialEntries={['/s/prep']}>{ui}</MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('Prep readiness header', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(getSummary).mockResolvedValue(SUMMARY)
    vi.mocked(listDocuments).mockResolvedValue([
      { id: 'doc-1', file_name: 'Transcript.pdf', file_size_bytes: 1000, document_type: 'transcript', verification_status: 'pending' },
    ])
    vi.mocked(getMyInterviews).mockResolvedValue([INTERVIEW])
    vi.mocked(listRecommendations).mockResolvedValue([RECOMMENDER])
  })

  it('promotes the highest-risk prep action and switches to its tab', async () => {
    renderPage(<PrepPage />)

    expect(screen.getByText('Prep readiness across prompts, materials, interviews, and letters')).toBeTruthy()
    expect(await screen.findByText('1 response')).toBeTruthy()
    expect(screen.getAllByText('Needs attention').length).toBeGreaterThan(0)
    expect(screen.getByText('1 invitation needs your answer.')).toBeTruthy()
    expect(screen.getByText('0/1 verified')).toBeTruthy()
    expect(screen.getByText('1 file still needs confirmation.')).toBeTruthy()
    expect(screen.getByText('Missing coverage: leadership')).toBeTruthy()

    fireEvent.click(screen.getByRole('button', { name: 'Respond to interviews: 1 invitation needs your answer.' }))

    await waitFor(() => expect(screen.getByText('Interviews tab')).toBeTruthy())
  })
})
