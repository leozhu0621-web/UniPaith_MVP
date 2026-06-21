import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

import GoalsTab from '../pages/student/profile/GoalsTab'
import NeedsTab from '../pages/student/profile/NeedsTab'
import * as goalsApi from '../api/goals'
import * as needsApi from '../api/needs'

vi.mock('../stores/toast-store', () => ({ showToast: vi.fn() }))

vi.mock('../api/goals', () => ({
  listGoals: vi.fn(),
  createGoal: vi.fn(),
  updateGoal: vi.fn(),
  deleteGoal: vi.fn(),
}))

vi.mock('../api/needs', () => ({
  listNeeds: vi.fn(),
  createNeed: vi.fn(),
  updateNeed: vi.fn(),
  deleteNeed: vi.fn(),
}))

function renderWithQuery(ui: React.ReactElement) {
  const qc = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  })
  return render(<QueryClientProvider client={qc}>{ui}</QueryClientProvider>)
}

beforeEach(() => {
  vi.clearAllMocks()
  vi.mocked(goalsApi.listGoals).mockResolvedValue([])
  vi.mocked(goalsApi.createGoal).mockResolvedValue({
    id: 'goal-1',
    student_id: 'student-1',
    category: 'social',
    specific: 'Build a peer support circle.',
    measurable: null,
    achievable_notes: null,
    relevant_notes: null,
    time_bound: null,
    status: 'active',
    source: 'manual',
    source_session_id: null,
    confidence: null,
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
  })
  vi.mocked(needsApi.listNeeds).mockResolvedValue([])
  vi.mocked(needsApi.createNeed).mockResolvedValue({
    id: 'need-1',
    student_id: 'student-1',
    maslow_level: 'self_esteem',
    need_type: 'Faculty mentorship',
    signal: 'I need close advisor access.',
    severity: 'must_have',
    source: 'manual',
    source_session_id: null,
    source_quote: null,
    confidence: null,
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
  })
})

describe('Profile goals and needs form controls', () => {
  it('uses the shared select control for goal category and submits the chosen value', async () => {
    renderWithQuery(<GoalsTab />)

    fireEvent.click(await screen.findByRole('button', { name: /add goal/i }))
    const dialog = await screen.findByRole('dialog', { name: /add goal/i })
    fireEvent.change(within(dialog).getByRole('combobox', { name: /category/i }), {
      target: { value: 'social' },
    })
    fireEvent.change(within(dialog).getByLabelText(/specific/i), {
      target: { value: 'Build a peer support circle.' },
    })
    fireEvent.click(within(dialog).getByRole('button', { name: /^add goal$/i }))

    await waitFor(() => {
      expect(goalsApi.createGoal).toHaveBeenCalledWith(expect.objectContaining({
        category: 'social',
        specific: 'Build a peer support circle.',
        status: 'active',
      }))
    })
  })

  it('uses shared select controls for need tier/severity and submits the chosen values', async () => {
    renderWithQuery(<NeedsTab />)

    fireEvent.click(await screen.findByRole('button', { name: /add need/i }))
    const dialog = await screen.findByRole('dialog', { name: /add need/i })
    fireEvent.change(within(dialog).getByRole('combobox', { name: /maslow tier/i }), {
      target: { value: 'self_esteem' },
    })
    fireEvent.change(within(dialog).getByRole('combobox', { name: /severity/i }), {
      target: { value: 'must_have' },
    })
    fireEvent.change(within(dialog).getByLabelText(/need type/i), {
      target: { value: 'Faculty mentorship' },
    })
    fireEvent.change(within(dialog).getByLabelText(/signal/i), {
      target: { value: 'I need close advisor access.' },
    })
    fireEvent.click(within(dialog).getByRole('button', { name: /^add need$/i }))

    await waitFor(() => {
      expect(needsApi.createNeed).toHaveBeenCalledWith(expect.objectContaining({
        maslow_level: 'self_esteem',
        need_type: 'Faculty mentorship',
        severity: 'must_have',
      }))
    })
  })
})
