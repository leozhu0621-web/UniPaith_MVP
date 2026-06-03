import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter } from 'react-router-dom'

import EvalHarnessPage from '../pages/public/EvalHarnessPage'
import * as buildApi from '../api/build'
import type { EvalHarness } from '../types/buildEvalHarness'

// Spec 62 — the /goal/eval-harness transparency surface. Renders the pluggable
// consumers (chatbot + extraction), their golden case counts + dimensions, the
// calibrated/independent judge, the four eval modes and the two added tables from
// GET /build/eval-harness.

const HARNESS: EvalHarness = {
  the_bar: {
    statement: 'An AI surface is good when it is good measurably.',
    principle: 'Build the evaluation once and share it.',
  },
  summary: {
    consumer_count: 3,
    consumers_live: 2,
    consumers_planned: 1,
    golden_case_total: 19,
    dimension_total: 11,
    hard_floor_dimension_count: 2,
    deterministic_check_total: 7,
    independent_judge_count: 1,
    judge_target_agreement: 0.85,
    suite_count: 2,
    suites_in_runner: 2,
    eval_mode_count: 4,
    modes_live: 1,
    new_table_count: 2,
    new_tables_present: 2,
    reused_table_count: 4,
    phase_count: 4,
    phases_live: 2,
    acceptance_count: 7,
    acceptance_live: 3,
    slo_count: 4,
    cost_control_count: 5,
    open_question_count: 4,
    backing_route_count: 26,
    config_knob_count: 3,
    provider: 'anthropic',
    live_is_source_of_truth: true,
  },
  consumers: [
    {
      key: 'chatbot',
      title: 'Chatbot',
      spec: '61',
      file: 'ai/evals/chatbot_adapter.py',
      status: 'live',
      golden_case_count: 10,
      golden_version: 'v1',
      hooks: {
        produce: 'Safety-screen then run the orchestrator.',
        rubric: 'The behavior constitution, verbatim.',
        materialize: 'A 👎 turn becomes a golden case.',
        materialize_source: '👎 ai_turn_feedback · escalations',
      },
      dimensions: [
        { key: 'groundedness', label: 'Groundedness', hard_floor: false, kind: 'judge', summary: 'Cite real data.' },
        { key: 'safety', label: 'Safety', hard_floor: true, kind: 'judge', summary: 'Escalate crises.' },
      ],
      deterministic_checks: [
        { name: 'no_generation', blurb: 'Never writes content for the student.' },
        { name: 'no_pii_leak', blurb: 'No email / phone / SSN in the reply.' },
      ],
      judge: {
        model: 'haiku',
        independent: false,
        system_under_test: 'orchestrator (Sonnet)',
        agreement: null,
        target_agreement: 0.85,
        status: 'baseline',
        note: 'Distinct model + slot from the agent under test.',
      },
    },
    {
      key: 'extraction',
      title: 'Extraction',
      spec: '60',
      file: 'ai/evals/extraction_adapter.py',
      status: 'live',
      golden_case_count: 9,
      golden_version: 'v1',
      hooks: {
        produce: 'Run the grounded SourceExtractionAgent.',
        rubric: 'Per-field P/R/F1, no-fabrication, schema-validity, normalization.',
        materialize: 'A correction becomes a golden page.',
        materialize_source: 'corrections · selector breaks',
      },
      dimensions: [
        { key: 'per_field_prf', label: 'Per-field P/R/F1', hard_floor: false, kind: 'deterministic', summary: 'F1 of emitted pairs.' },
        { key: 'no_fabrication', label: 'No fabrication', hard_floor: true, kind: 'deterministic', summary: 'Grounded + in schema.' },
      ],
      deterministic_checks: [
        { name: 'no_fabrication', blurb: 'Grounded in source + schema allowlist.' },
        { name: 'schema_validity', blurb: 'No field outside the schema.' },
      ],
      judge: {
        model: 'claude (sonnet)',
        independent: true,
        system_under_test: 'Qwen / deterministic extractor',
        agreement: null,
        target_agreement: 0.85,
        status: 'baseline',
        note: 'Claude judges the Qwen extraction.',
      },
    },
    {
      key: 'match_rationale',
      title: 'Match rationale',
      spec: '45',
      file: null,
      status: 'planned',
      golden_case_count: 0,
      golden_version: null,
      hooks: {
        produce: 'Generate a program-match rationale.',
        rubric: 'Factual support, no-fabrication, explainability.',
        materialize: 'A rationale 👎 becomes a golden case.',
        materialize_source: 'rationale 👎 · contested matches',
      },
      dimensions: [],
      deterministic_checks: [],
      judge: null,
    },
  ],
  adapter_hooks: [
    { hook: 'produce(case)', blurb: 'Run the agent / extractor on a case.' },
    { hook: 'rubric()', blurb: 'The scored dimensions + the judge prompt.' },
    { hook: 'materialize(event)', blurb: 'A production failure → a golden case.' },
  ],
  eval_modes: [
    { n: 1, key: 'ci_gate', title: 'CI gate (offline)', blurb: 'Block on a regression or hard-floor breach.', status: 'live', backing_table: 'evaluation_runs', backing_table_present: true },
    { n: 2, key: 'ab', title: 'Pre-promote A/B', blurb: 'Roll a variant to a cohort.', status: 'partial', backing_table: 'ab_test_assignments', backing_table_present: true },
    { n: 3, key: 'sampling', title: 'Production sampling', blurb: 'Sample live outputs.', status: 'planned', backing_table: 'ai_turns', backing_table_present: true },
    { n: 4, key: 'drift', title: 'Scheduled drift', blurb: 'Re-run on a cadence.', status: 'partial', backing_table: 'drift_snapshots', backing_table_present: true },
  ],
  suites: [
    { key: 'extraction_no_fabrication', title: 'Extraction · no fabrication', hard_floor: true, blurb: 'Every field grounded.', in_runner: true, threshold: { min_pass_rate: 1.0 } },
    { key: 'extraction_accuracy_v2', title: 'Extraction · per-field F1', hard_floor: false, blurb: 'Mean per-field F1.', in_runner: true, threshold: { min_f1: 0.85 } },
  ],
  data_model: {
    new_tables: [
      { name: 'eval_cases', blurb: 'The versioned golden set.', present: true, column_count: 12 },
      { name: 'eval_results', blurb: 'Per-case-per-run scores.', present: true, column_count: 11 },
    ],
    reused_tables: [
      { name: 'evaluation_runs', blurb: 'Each eval run + its metrics.', present: true, column_count: 14 },
      { name: 'drift_snapshots', blurb: 'Drift snapshots.', present: true, column_count: 13 },
    ],
  },
  synthetic_redteam: [
    { key: 'synthetic', title: 'Synthetic case generation', status: 'partial', blurb: 'Edge personas / malformed pages.' },
    { key: 'redteam', title: 'Red-team battery', status: 'live', blurb: 'Any pass blocks.' },
  ],
  slos: [
    { text: 'No golden-set regression ships.', status: 'live' },
    { text: 'Judge ↔ expert agreement ≥ 85%.', status: 'partial' },
  ],
  cost_controls: [
    { text: 'Deterministic checks run before the LLM-judge.', status: 'live' },
  ],
  phases: [
    { key: 'A', title: 'Primitives + chatbot', blurb: 'Case store + judge + runner + CI gate.', status: 'live' },
    { key: 'B', title: 'Extraction adapter', blurb: 'A second consumer reuses the harness.', status: 'live' },
  ],
  acceptance: [
    { status: 'live', text: 'One service; chatbot + extraction via adapters.' },
    { status: 'partial', text: 'Golden sets versioned and CI-gated.' },
  ],
  open_questions: [{ q: 'Build vs buy the judge', a: 'Keep golden sets in-house.' }],
  config_knobs: [{ name: 'ai_provider_default', value: 'anthropic', section: '§4' }],
  routes: {
    chatbot: ['/api/v1/students/me/discovery/sessions'],
    extraction: ['/api/v1/reference/occupations'],
  },
  tiers: { extractor: 'batch', validator: 'batch', orchestrator: 'workhorse' },
}

function renderPage() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter initialEntries={['/goal/eval-harness']}>
        <EvalHarnessPage />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('Spec 62 — the /goal/eval-harness surface', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('renders the consumers, dimensions, modes and added tables', async () => {
    vi.spyOn(buildApi, 'getEvalHarness').mockResolvedValue(HARNESS)
    renderPage()

    expect(screen.getByText(/One harness\. Every AI surface, measured\./i)).toBeInTheDocument()
    // Both live consumers render (the title appears in the consumer, judge and
    // deterministic-checks cards, so assert at least one).
    await waitFor(() => expect(screen.getAllByText('Chatbot').length).toBeGreaterThan(0))
    expect(screen.getAllByText('Extraction').length).toBeGreaterThan(0)
    // The extraction hard-floor dimension renders with its badge.
    expect(screen.getByText('No fabrication')).toBeInTheDocument()
    expect(screen.getAllByText('Hard floor').length).toBeGreaterThan(0)
    // The CI gate mode renders.
    expect(screen.getByText('CI gate (offline)')).toBeInTheDocument()
    // The two added tables render, flagged New.
    expect(screen.getByText('eval_cases')).toBeInTheDocument()
    expect(screen.getByText('eval_results')).toBeInTheDocument()
    expect(screen.getAllByText('New').length).toBeGreaterThan(0)
    // The independent-judge proof shows.
    expect(screen.getAllByText('Independent').length).toBeGreaterThan(0)
    // The gold beat.
    expect(screen.getByText(/2 consumers · one harness/i)).toBeInTheDocument()
  })

  it('filters the consumers to live only', async () => {
    vi.spyOn(buildApi, 'getEvalHarness').mockResolvedValue(HARNESS)
    renderPage()

    await waitFor(() => expect(screen.getByText('Match rationale')).toBeInTheDocument())
    fireEvent.click(screen.getByRole('button', { name: 'Live only' }))
    await waitFor(() => expect(screen.queryByText('Match rationale')).not.toBeInTheDocument())
    // The live consumers stay (title appears across cards → assert at least one).
    expect(screen.getAllByText('Chatbot').length).toBeGreaterThan(0)
    expect(screen.getAllByText('Extraction').length).toBeGreaterThan(0)
  })

  it('shows an error state with a retry when the fetch fails', async () => {
    vi.spyOn(buildApi, 'getEvalHarness').mockRejectedValue(new Error('boom'))
    renderPage()
    await waitFor(() =>
      expect(screen.getByText(/couldn't load the eval-harness surface/i)).toBeInTheDocument(),
    )
    expect(screen.getByRole('button', { name: 'Retry' })).toBeInTheDocument()
  })
})
