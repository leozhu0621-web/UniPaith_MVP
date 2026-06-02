import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter } from 'react-router-dom'

import ClaudeApiGoalPage from '../pages/public/ClaudeApiGoalPage'
import * as aiAgentsApi from '../api/aiAgents'
import type { AiAgentCatalog } from '../types/aiAgents'

// Spec 45 — the public /goal/claude-api transparency page. Renders the live
// agent catalog from GET /api/v1/ai/agents and lets the visitor filter it.

const CATALOG: AiAgentCatalog = {
  summary: {
    agent_count: 2,
    llm_agent_count: 2,
    tier_counts: { flagship: 1, workhorse: 1, batch: 0, rule_based: 0 },
    fallback_coverage: '100%',
    provider: 'anthropic',
  },
  tiers: [
    {
      tier: 'flagship',
      label: 'Opus',
      role: 'High-stakes single shots.',
      model_id: 'claude-opus-4-8',
      price: { input: 15, output: 75 },
      agent_count: 1,
    },
    {
      tier: 'workhorse',
      label: 'Sonnet',
      role: 'The default tier.',
      model_id: 'claude-sonnet-4-6',
      price: { input: 3, output: 15 },
      agent_count: 1,
    },
  ],
  agents: [
    {
      name: 'rationale',
      title: 'Match Rationale',
      spec_sections: ['§6'],
      surface: 'student',
      group: 'Match',
      purpose: 'Explains why a program was recommended.',
      tier: 'workhorse',
      tier_label: 'Sonnet',
      model_id: 'claude-sonnet-4-6',
      consent: 'matching',
      consent_label: 'Matching consent',
      mode: 'json',
      streaming: false,
      cache: { system: '1h', persona: '5min' },
      fallback: 'Template rationale.',
      flag: 'ai_match_rationale_v2_enabled',
      enabled: true,
      prompt_file: 'rationale.md',
    },
    {
      name: 'review_summarizer',
      title: 'Review Packet Summarizer',
      spec_sections: ['§14'],
      surface: 'institution',
      group: 'Review',
      purpose: 'Opus per-applicant packet summary for reviewers.',
      tier: 'flagship',
      tier_label: 'Opus',
      model_id: 'claude-opus-4-8',
      consent: null,
      consent_label: 'No student-data gate',
      mode: 'tool_use',
      streaming: false,
      cache: { system: '1h', persona: '5min' },
      fallback: 'Template summary from rule-based extraction.',
      flag: null,
      enabled: true,
      prompt_file: null,
    },
  ],
  principles: [
    { title: 'Humans decide', body: 'Every agent informs a person.' },
    { title: 'Evidence-linked', body: 'References specific signals.' },
    { title: 'Consent-gated', body: 'The mask is resolved before every call.' },
    { title: 'Always falls back', body: 'Never a 5xx.' },
  ],
  fallback_flow: [{ trigger: 'Provider 5xx / timeout', action: 'Fail over, then rule-based.' }],
  cache_strategy: [
    { layer: 'System block', ttl: '1 hour', note: 'Stable instructions.' },
    { layer: 'Persona block', ttl: '5 minutes', note: 'Profile context.' },
    { layer: 'Per-turn tail', ttl: 'Uncached', note: 'The volatile message.' },
  ],
  validation: { summary: 'Pydantic v2 validates every output.', steps: ['Validate', 'Retry once'] },
}

function renderPage() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter initialEntries={['/goal/claude-api']}>
        <ClaudeApiGoalPage />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('Spec 45 — Claude API goal page', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('renders the hero, model tiers, and the live agent inventory', async () => {
    vi.spyOn(aiAgentsApi, 'getAiAgents').mockResolvedValue(CATALOG)
    renderPage()

    // Static hero copy paints immediately (before the query resolves).
    expect(screen.getByText(/Every assistive feature, powered by Claude/i)).toBeInTheDocument()
    expect(screen.getByText(/Three Claude tiers/i)).toBeInTheDocument()

    // Data-driven content appears once the catalog loads.
    await waitFor(() => expect(screen.getByText('Match Rationale')).toBeInTheDocument())
    expect(screen.getByText('Review Packet Summarizer')).toBeInTheDocument()
    expect(screen.getAllByText(/claude-sonnet-4-6/).length).toBeGreaterThan(0)
    expect(screen.getByText(/AI agents in production/i)).toBeInTheDocument()
  })

  it('filters the inventory by surface', async () => {
    vi.spyOn(aiAgentsApi, 'getAiAgents').mockResolvedValue(CATALOG)
    renderPage()
    await waitFor(() => expect(screen.getByText('Match Rationale')).toBeInTheDocument())

    fireEvent.click(screen.getByRole('button', { name: 'Institution' }))

    await waitFor(() => expect(screen.queryByText('Match Rationale')).not.toBeInTheDocument())
    expect(screen.getByText('Review Packet Summarizer')).toBeInTheDocument()
  })
})
