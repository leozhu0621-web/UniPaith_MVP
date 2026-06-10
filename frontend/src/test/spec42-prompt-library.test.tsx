import type { ReactElement } from 'react'
import { describe, expect, it, vi } from 'vitest'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

import {
  COMPETENCIES,
  COMPETENCY_LABELS,
  DRAFT_META,
  INTENT_LABELS,
  previewStar,
  starCount,
  wordCount,
} from '../pages/student/apply/promptlibrary/constants'
import type {
  BehavioralPrompt,
  PromptLibrarySummary,
  Story,
} from '../types/promptLibrary'

const STAR_ANSWER =
  'During my junior year our robotics team was failing. My goal was to rebuild morale. ' +
  'So I organized weekly stand-ups and I rewrote the build plan. As a result we placed 2nd ' +
  'regionally, up from 11th. Looking back, I learned that small wins compound.'

// ── Pure helpers (client STAR preview must mirror the backend) ────────────────

describe('Spec 42 — Prompt Library client helpers', () => {
  it('previewStar lights all five elements on a complete STAR answer', () => {
    const f = previewStar(STAR_ANSWER)
    expect(f.situation).toBe(true)
    expect(f.task).toBe(true)
    expect(f.action).toBe(true)
    expect(f.result).toBe(true)
    expect(f.reflection).toBe(true)
    expect(starCount(f)).toBe(5)
  })

  it('previewStar is empty-safe', () => {
    expect(starCount(previewStar(''))).toBe(0)
    expect(wordCount('')).toBe(0)
    expect(wordCount('two words')).toBe(2)
  })

  it('label maps cover every competency + a base intent set', () => {
    COMPETENCIES.forEach(c => expect(COMPETENCY_LABELS[c]).toBeTruthy())
    for (const intent of ['leadership', 'failure', 'fit', 'vision', 'ethics']) {
      expect(INTENT_LABELS[intent]).toBeTruthy()
    }
    expect(DRAFT_META.final.variant).toBe('success')
  })
})

// ── Render smoke (feedback-only invariant) ────────────────────────────────────

vi.mock('../api/prompt-library', () => ({
  listPrompts: vi.fn().mockResolvedValue([
    {
      prompt_key: 'proudest_accomplishment',
      title: 'Your proudest accomplishment',
      intent_tag: 'impact',
      target_channel: 'interview',
      time_limit_seconds: 180,
      word_limit: null,
      format_required: 'STAR',
      evidence_required_flag: true,
      allowed_attachments_flag: false,
      language_option: 'en',
      confidentiality_scope: 'private',
      reuse_allowed_flag: 'core',
      sort_order: 0,
    } as BehavioralPrompt,
  ]),
  listResponses: vi.fn().mockResolvedValue([]),
  listStories: vi.fn().mockResolvedValue([]),
  getSummary: vi.fn().mockResolvedValue({
    total_prompts: 1,
    answered_count: 0,
    final_count: 0,
    draft_count: 0,
    stories_count: 0,
    inference_enabled: true,
    interview_readiness_band: 'low',
    interview_readiness_score: 0,
    readiness_detail: { band: 'low', score: 0, answered: 0, core_total: 8, star_avg: 0 },
    competency_coverage_map: { leadership: 0, teamwork: 0 },
    competency_coverage_gaps: ['leadership', 'teamwork'],
    story_prompt_matching_table: [],
    revision_priority_list: [],
    suggested_practice_plan: 'Start with the core interview set.',
  } as PromptLibrarySummary),
  createStory: vi.fn().mockResolvedValue({}),
  updateStory: vi.fn().mockResolvedValue({}),
  deleteStory: vi.fn().mockResolvedValue(undefined),
  upsertResponse: vi.fn().mockResolvedValue({}),
}))

import { updateStory } from '../api/prompt-library'
import PromptLibraryTab from '../pages/student/apply/promptlibrary/PromptLibraryTab'
import StoryEditor from '../pages/student/apply/promptlibrary/StoryEditor'

function renderTab(ui: ReactElement) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>{ui}</MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('Spec 42 — Prompt Library tab renders, never ghost-writes', () => {
  it('shows the catalog + readiness, and exposes no generate/write-for-me button', async () => {
    renderTab(<PromptLibraryTab />)

    expect(screen.getByText('Prompt Library')).toBeTruthy()
    await waitFor(() => expect(screen.getByText('Your proudest accomplishment')).toBeTruthy())

    const labels = screen.getAllByRole('button').map(b => (b.textContent ?? '').toLowerCase())
    // Feedback-only ethos — coach structure, never write the answer.
    expect(labels.some(t => /generate|write (my|your)|rewrite|model answer/.test(t))).toBe(false)
  })
})

// ── Story editor — editing must round-trip every saved field ──────────────────

const EXISTING_STORY: Story = {
  id: 'story-1',
  title: 'Rebuilt a failing robotics team',
  summary: 'Took over a struggling team and turned the season around.',
  primary_competency: 'leadership',
  secondary_competency: null,
  competency_tags: ['leadership'],
  context_tags: ['school'],
  role_type: 'leader',
  stakeholder_type: 'peers',
  conflict_type: null,
  difficulty_tier: 3,
  recency: null,
  duration: '6 months',
  scale_tier: 2,
  evidence_link: null,
  referenceable_contact_flag: true,
  source: 'student-typed',
  confidence: 70,
  record_version: 1,
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-01T00:00:00Z',
}

describe('Spec 42 — StoryEditor edit round-trip', () => {
  it('saving an untouched edit preserves stakeholder_type (PUT is a full replace)', async () => {
    renderTab(<StoryEditor story={EXISTING_STORY} isOpen onClose={() => {}} />)

    fireEvent.click(screen.getByRole('button', { name: 'Save changes' }))

    await waitFor(() => expect(updateStory).toHaveBeenCalled())
    expect(updateStory).toHaveBeenCalledWith(
      'story-1',
      expect.objectContaining({
        title: 'Rebuilt a failing robotics team',
        role_type: 'leader',
        stakeholder_type: 'peers',
      }),
    )
  })
})
