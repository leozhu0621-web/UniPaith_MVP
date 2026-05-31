import type { ReactElement } from 'react'
import { describe, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

// No network in tests — the panels mount a program picker that queries
// /applications/me, and the CTA would POST feedback. Stub both.
vi.mock('../api/workshops-feedback', () => ({
  requestEssayFeedback: vi.fn(),
  requestInterviewPractice: vi.fn(),
  requestTestGuidance: vi.fn(),
  listWorkshopRuns: vi.fn(),
}))
vi.mock('../api/applications', () => ({
  listMyApplications: vi.fn().mockResolvedValue([]),
}))

import EssayFeedbackPanel from '../pages/student/apply/EssayFeedbackPanel'
import InterviewPracticePanel from '../pages/student/apply/InterviewPracticePanel'

function renderPanel(ui: ReactElement) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(<QueryClientProvider client={qc}>{ui}</QueryClientProvider>)
}

const buttonLabels = () =>
  screen.getAllByRole('button').map(b => (b.textContent ?? '').toLowerCase())

describe('Spec 14 — Workshops are feedback-only (UI invariant)', () => {
  it('essay panel: empty hint + cobalt "Get feedback" CTA, never a generate/rewrite button', () => {
    renderPanel(<EssayFeedbackPanel />)

    // Spec §8 / §13 empty-state copy.
    expect(screen.getByText('Drop in an essay draft to get structured feedback.')).toBeTruthy()

    const labels = buttonLabels()
    expect(labels.some(t => t.includes('get feedback'))).toBe(true)
    expect(labels.some(t => /generate|rewrite|write (my|your)|model answer/.test(t))).toBe(false)

    // Spec §10 — the CTA is the cobalt secondary variant, never gold (primary).
    const cta = screen.getByRole('button', { name: /get feedback/i })
    expect(cta.className).toContain('bg-secondary')
    expect(cta.className).not.toContain('bg-primary')
  })

  it('interview panel: CTA never says "Generate"; surfaces the practice-not-answers promise', () => {
    renderPanel(<InterviewPracticePanel />)

    const labels = buttonLabels()
    // Generation of *questions* is allowed, but the copy rule (§13) bans "Generate".
    expect(labels.some(t => t.includes('get practice questions'))).toBe(true)
    expect(labels.some(t => t.includes('generate'))).toBe(false)

    expect(screen.getByText(/these are practice questions, not answers\./i)).toBeTruthy()
  })
})
