// UX overhaul Ship C §3 — full-scale onboarding: needs-rule, draft fallback,
// intake-term generator, and the Imprint wizard's render / advance / resume.
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

import {
  needsOnboarding,
  mergeWithLocalDraft,
  writeLocalDraft,
  clearLocalDraft,
  ONBOARDING_DRAFT_KEY,
} from '../pages/student/onboarding/onboarding-state'
import { nextIntakeTerms } from '../pages/student/onboarding/catalog'
import OnboardingPage from '../pages/student/OnboardingPage'

vi.mock('../api/students', () => ({
  getProfile: vi.fn(),
  patchOnboardingState: vi.fn(),
}))
import { getProfile, patchOnboardingState } from '../api/students'

const getProfileMock = vi.mocked(getProfile)
const patchMock = vi.mocked(patchOnboardingState)

function renderWizard() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={['/onboarding']}>
        <OnboardingPage />
      </MemoryRouter>
    </QueryClientProvider>
  )
}

beforeEach(() => {
  clearLocalDraft()
  patchMock.mockResolvedValue({})
  // Collapse the wizard's JS hold timers (select → advance, build moment).
  document.documentElement.setAttribute('data-reduce-motion', '')
})

afterEach(() => {
  document.documentElement.removeAttribute('data-reduce-motion')
  vi.clearAllMocks()
})

describe('needsOnboarding (contract §4)', () => {
  it('is false for non-students', () => {
    expect(needsOnboarding('institution_admin', null)).toBe(false)
    expect(needsOnboarding(undefined, null)).toBe(false)
  })

  it('treats null AND a missing field as needs-onboarding', () => {
    expect(needsOnboarding('student', null)).toBe(true)
    expect(needsOnboarding('student', undefined)).toBe(true)
    expect(needsOnboarding('student', {})).toBe(true)
  })

  it('completed_at or dismissed_at ends the need', () => {
    expect(needsOnboarding('student', { completed_at: '2026-06-12T00:00:00Z' })).toBe(false)
    expect(needsOnboarding('student', { dismissed_at: '2026-06-12T00:00:00Z' })).toBe(false)
  })

  it('honors LOCAL completed/dismissed stamps when the backend lacks the column', () => {
    writeLocalDraft({ dismissed: true })
    expect(needsOnboarding('student', null)).toBe(false)
    expect(needsOnboarding('student', undefined)).toBe(false)
  })
})

describe('local draft (deploy-ordering fallback)', () => {
  it('merges answers key-wise and stamps idempotently', () => {
    writeLocalDraft({ answers: { stage: 'exploring' }, last_step: 1 })
    writeLocalDraft({ answers: { degree_level: 'masters' }, last_step: 3 })
    const draft = mergeWithLocalDraft(null)
    expect(draft.answers).toEqual({ stage: 'exploring', degree_level: 'masters' })
    expect(draft.last_step).toBe(3)
    expect(localStorage.getItem(ONBOARDING_DRAFT_KEY)).toBeTruthy()
  })

  it('overlays the draft on server state (draft is the newer failed write)', () => {
    writeLocalDraft({ answers: { intake_term: 'Fall 2027' }, last_step: 4 })
    const merged = mergeWithLocalDraft({ answers: { stage: 'building_list' }, last_step: 2 })
    expect(merged.answers).toEqual({ stage: 'building_list', intake_term: 'Fall 2027' })
    expect(merged.last_step).toBe(4)
  })
})

describe('nextIntakeTerms', () => {
  it('June → leads with this Fall, alternating', () => {
    expect(nextIntakeTerms(6, new Date('2026-06-12T12:00:00'))).toEqual([
      'Fall 2026', 'Spring 2027', 'Fall 2027', 'Spring 2028', 'Fall 2028', 'Spring 2029',
    ])
  })

  it('September → leads with next Spring', () => {
    expect(nextIntakeTerms(3, new Date('2026-09-01T12:00:00'))).toEqual([
      'Spring 2027', 'Fall 2027', 'Spring 2028',
    ])
  })
})

describe('OnboardingPage wizard', () => {
  it('renders welcome, advances to stage, autosaves the selection', async () => {
    getProfileMock.mockResolvedValue({ first_name: 'Leo', onboarding_state: null })
    renderWizard()

    expect(await screen.findByText(/let's set up your space/i)).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: /get started/i }))

    expect(await screen.findByText('What stage are you at?')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('radio', { name: /just exploring/i }))

    // Single-select auto-advances (reduced-motion → instant) and PATCHes.
    expect(await screen.findByText('Which fields interest you?')).toBeInTheDocument()
    await waitFor(() => {
      expect(patchMock).toHaveBeenCalledWith(
        expect.objectContaining({ answers: expect.objectContaining({ stage: 'exploring' }) })
      )
    })
  })

  it('resumes from onboarding_state.last_step', async () => {
    getProfileMock.mockResolvedValue({
      onboarding_state: { answers: { stage: 'ready_to_apply' }, last_step: 3 },
    })
    renderWizard()
    expect(await screen.findByText('What degree level?')).toBeInTheDocument()
  })

  it('keeps answers locally when the backend lacks the endpoint (PATCH 404)', async () => {
    getProfileMock.mockResolvedValue({ onboarding_state: null })
    patchMock.mockRejectedValue(Object.assign(new Error('404'), { response: { status: 404 } }))
    renderWizard()

    fireEvent.click(await screen.findByRole('button', { name: /get started/i }))
    fireEvent.click(await screen.findByRole('radio', { name: /just exploring/i }))
    await screen.findByText('Which fields interest you?')

    const draft = mergeWithLocalDraft(null)
    expect(draft.answers?.stage).toBe('exploring')
  })
})
