import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter } from 'react-router-dom'

import ChatbotEvalPage from '../pages/public/ChatbotEvalPage'
import * as buildApi from '../api/build'
import type { ChatbotEval } from '../types/build'

// Spec 61 — the /goal/chatbot-eval transparency surface. Renders the constitution
// dimensions, the eval suites with their live case counts, the two Claude agents,
// the safety floor and the build-task checklist from GET /build/chatbot-eval.

const CHATBOT_EVAL: ChatbotEval = {
  the_bar: { statement: 'Good is measured, not asserted.', principle: 'Steered and graded by the same words.' },
  summary: {
    agent_count: 2,
    constitution_count: 2,
    constitutions_present: true,
    constitution_version: '1.0.0',
    dimension_count: 7,
    hard_floor_count: 1,
    suite_count: 4,
    suites_live: 4,
    hard_floor_suite_count: 2,
    golden_case_total: 44,
    deterministic_check_count: 5,
    loop_stage_count: 8,
    loop_stages_live: 3,
    build_task_count: 8,
    tasks_live: 5,
    tasks_partial: 3,
    tasks_planned: 0,
    acceptance_count: 6,
    acceptance_live: 4,
    safety_crisis_subtype_count: 3,
    safety_harmful_subtype_count: 4,
    backing_route_count: 19,
    config_knob_count: 4,
    open_question_count: 1,
    provider: 'anthropic',
    all_agents_claude: true,
    live_is_source_of_truth: true,
  },
  constitutions: [
    {
      agent: 'student',
      present: true,
      version: '1.0.0',
      dimension_count: 7,
      hard_floor_keys: ['safety'],
      dimensions: [
        { key: 'groundedness', label: 'Groundedness', hard_floor: false, summary: 'Cite real data; admit gaps.' },
        { key: 'safety', label: 'Safety & crisis floor', hard_floor: true, summary: 'Escalate crises to a human.' },
        { key: 'tone', label: 'Tone', hard_floor: false, summary: 'Concrete reflection over empty validation.' },
      ],
    },
    { agent: 'faculty', present: true, version: '1.0.0', dimension_count: 7, hard_floor_keys: ['safety'], dimensions: [] },
  ],
  agents: [
    {
      key: 'student_advisor',
      title: 'Student advisor',
      spec: '19',
      file: 'ai/orchestrator.py',
      surface: 'discovery',
      agent_name: 'orchestrator',
      tier: 'workhorse',
      provider: 'anthropic',
      role: 'Counsels one student through Discovery.',
      blurb: 'Never recommends programs in Discovery.',
    },
    {
      key: 'faculty_assistant',
      title: 'Faculty / institution assistant',
      spec: '37',
      file: 'ai/institution_reply.py',
      surface: 'institution_reply',
      agent_name: 'institution_reply_drafter',
      tier: 'batch',
      provider: 'anthropic',
      role: 'Drafts inbox replies for staff.',
      blurb: 'Drafts never decide.',
    },
  ],
  loop_stages: [
    { n: 1, key: 'sample', title: 'Sample', blurb: 'Pull production turns.', status: 'partial' },
    { n: 2, key: 'judge', title: 'Judge', blurb: 'Deterministic floor, then the judge.', status: 'live' },
  ],
  eval_suites: [
    { key: 'constitution_adherence', title: 'Constitution adherence', section: '§3/§5', status: 'live', hard_floor: false, blurb: 'Golden cases per dimension.', case_count: 10, in_runner: true },
    { key: 'safety_crisis', title: 'Safety & crisis', section: '§4', status: 'live', hard_floor: true, blurb: 'Crisis recall + false-positive guard.', case_count: 14, in_runner: true },
    { key: 'redteam', title: 'Red-team battery', section: '§7', status: 'live', hard_floor: true, blurb: 'Any pass blocks.', case_count: 17, in_runner: true },
  ],
  safety: {
    always_on: true,
    status: 'live',
    crisis_subtypes: ['self_harm', 'abuse', 'acute_distress'],
    harmful_subtypes: ['essay_generation', 'admission_guarantee', 'jailbreak', 'pii_extraction'],
    crisis_pattern_count: 3,
    harmful_pattern_count: 4,
    note: 'Always on; escalates to a human / crisis resource.',
  },
  deterministic_checks: [
    { name: 'no_generation', blurb: 'Never writes content for the student.' },
    { name: 'no_pii_leak', blurb: 'No email / phone / SSN in the reply.' },
  ],
  build_tasks: [
    { section: '§10', status: 'live', text: 'Constitution files wired into the prompt + rubric', evidence: 'Parsed + included.' },
    { section: '§10', status: 'partial', text: 'Production sample→judge job', evidence: 'Needs traffic.' },
  ],
  acceptance: [
    { status: 'live', text: 'Per-agent constitution files exist, versioned, and ARE the rubric.' },
    { status: 'partial', text: 'The sample→judge→curate→improve→gate loop runs.' },
  ],
  config_knobs: [{ name: 'ai_provider_default', value: 'anthropic', section: '§2' }],
  routes: {
    discovery: ['/api/v1/students/me/discovery/sessions'],
    institution_reply: ['/api/v1/institutions/me/inbox/threads/{thread_id}/ai-draft'],
  },
  open_questions: [{ q: 'Multilingual standard', a: 'Add per-language golden cases.' }],
}

function renderPage() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter initialEntries={['/goal/chatbot-eval']}>
        <ChatbotEvalPage />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('Spec 61 — the /goal/chatbot-eval surface', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('renders the constitution dimensions, agents, suites and safety floor', async () => {
    vi.spyOn(buildApi, 'getChatbotEval').mockResolvedValue(CHATBOT_EVAL)
    renderPage()

    expect(screen.getByText(/The chatbot, held to a measured standard/i)).toBeInTheDocument()
    // Both Claude agents render.
    await waitFor(() => expect(screen.getByText('Student advisor')).toBeInTheDocument())
    expect(screen.getByText('Faculty / institution assistant')).toBeInTheDocument()
    // Constitution dimensions render with their hard-floor badge. ("Safety &
    // crisis floor" appears as both the dimension card and the deep-dive section
    // heading, so assert at least one is present.)
    expect(screen.getByText('Groundedness')).toBeInTheDocument()
    expect(screen.getAllByText('Safety & crisis floor').length).toBeGreaterThan(0)
    expect(screen.getAllByText('Hard floor').length).toBeGreaterThan(0)
    // Eval suites render with their live case counts.
    expect(screen.getByText('safety_crisis')).toBeInTheDocument()
    expect(screen.getByText('17 cases')).toBeInTheDocument()
    // The safety floor lists crisis + harmful subtypes.
    expect(screen.getByText('self_harm')).toBeInTheDocument()
    expect(screen.getByText('essay_generation')).toBeInTheDocument()
    // The provider-proof gold beat shows.
    expect(screen.getByText(/Both agents are Claude/i)).toBeInTheDocument()
  })

  it('filters the constitution dimensions to the hard floor', async () => {
    vi.spyOn(buildApi, 'getChatbotEval').mockResolvedValue(CHATBOT_EVAL)
    renderPage()

    await waitFor(() => expect(screen.getByText('Groundedness')).toBeInTheDocument())
    // Filter to hard-floor only → the scored dimensions drop out, safety stays.
    fireEvent.click(screen.getByRole('button', { name: 'Hard floor only' }))
    await waitFor(() => expect(screen.queryByText('Groundedness')).not.toBeInTheDocument())
    expect(screen.getAllByText('Safety & crisis floor').length).toBeGreaterThan(0)
  })

  it('shows an error state with a retry when the fetch fails', async () => {
    vi.spyOn(buildApi, 'getChatbotEval').mockRejectedValue(new Error('boom'))
    renderPage()
    await waitFor(() =>
      expect(screen.getByText(/couldn't load the chatbot eval surface/i)).toBeInTheDocument(),
    )
    expect(screen.getByRole('button', { name: 'Retry' })).toBeInTheDocument()
  })
})
