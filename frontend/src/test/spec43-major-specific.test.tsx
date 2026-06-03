import type { ReactElement } from 'react'
import { describe, expect, it, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

import { BAND_META, RATING_LABELS, trackLabel } from '../pages/student/apply/majorspecific/constants'

// ── Pure display constants ────────────────────────────────────────────────────

describe('Spec 43 — major-specific constants', () => {
  it('band meta covers all three readiness bands, gold only at high', () => {
    expect(BAND_META.high.text).toContain('primary')
    expect(BAND_META.medium.text).toContain('secondary')
    expect(BAND_META.low.text).toContain('warning')
  })

  it('rating labels are 1-indexed 1..5', () => {
    expect(RATING_LABELS[1]).toBe('None')
    expect(RATING_LABELS[5]).toBe('Expert')
  })

  it('trackLabel falls back to title-case', () => {
    expect(trackLabel('cs_data_ai')).toBe('Cs Data Ai')
    expect(trackLabel('cs_data_ai', 'Computer Science · Data · AI')).toBe(
      'Computer Science · Data · AI',
    )
  })
})

// ── Render smoke (feedback-only invariant) ────────────────────────────────────
// Fixtures live inside vi.hoisted so the hoisted vi.mock factory can reference
// them without a TDZ error.
const fx = vi.hoisted(() => {
  const coach = {
    track_key: 'cs_data_ai',
    major_track_fit_score: 72,
    completeness: 50,
    readiness_band: 'high',
    coding_readiness_band: 'high',
    project_coverage_map: {
      'CS fundamentals (self-rating)': 80,
      'Evidence & competitive': 50,
    },
    skill_gap_severity: 'low',
    specialization_match_tags: ['SWE'],
    gaps: [],
    suggested_artifacts_to_add: ['Add a public GitHub with at least one substantial project.'],
    track_recommendation: 'SWE',
    suggested_bridge_plan: 'You are well-prepared. Keep your strongest evidence current.',
  }
  const trackRow = {
    track_key: 'cs_data_ai',
    label: 'Computer Science · Data · AI',
    signals: { cs_fundamentals_self_rating_dsa: 4 },
    source: 'student-typed',
    confidence: 95,
    record_version: 1,
    updated_at: '2026-06-01T00:00:00Z',
    coach,
  }
  return {
    CATALOG: {
      suggested_tracks: ['cs_data_ai'],
      tracks: [
        {
          track_key: 'cs_data_ai',
          label: 'Computer Science · Data · AI',
          blurb: 'Programming, CS fundamentals, ML/data readiness.',
          groups: [
            {
              key: 'fundamentals',
              label: 'CS fundamentals (self-rating)',
              fields: [
                {
                  key: 'cs_fundamentals_self_rating_dsa',
                  label: 'Data structures & algorithms',
                  kind: 'rating_1_5',
                  max: 5,
                },
              ],
            },
            {
              key: 'evidence',
              label: 'Evidence & competitive',
              fields: [{ key: 'github_link', label: 'GitHub profile', kind: 'link' }],
            },
          ],
        },
      ],
    },
    TRACKS: {
      active_tracks: ['cs_data_ai'],
      suggested_tracks: ['cs_data_ai'],
      tracks: [trackRow],
    },
    SUMMARY: {
      active_track_count: 1,
      inference_enabled: true,
      primary_track: 'cs_data_ai',
      major_track_fit_score_per_target_track: { cs_data_ai: 72 },
      tracks: null,
    },
  }
})

vi.mock('../api/major-specific', () => ({
  getCatalog: vi.fn().mockResolvedValue(fx.CATALOG),
  getTracks: vi.fn().mockResolvedValue(fx.TRACKS),
  getSummary: vi.fn().mockResolvedValue(fx.SUMMARY),
  upsertTrack: vi.fn().mockResolvedValue(fx.TRACKS.tracks[0]),
}))

import MajorSpecificPanel from '../pages/student/apply/majorspecific/MajorSpecificPanel'

function renderPanel(ui: ReactElement) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(<QueryClientProvider client={qc}>{ui}</QueryClientProvider>)
}

describe('Spec 43 — major-specific panel renders readiness, never fills the field', () => {
  it('shows fit score, coverage, suggested evidence, and the track form', async () => {
    renderPanel(<MajorSpecificPanel />)

    // Wait for data to load — the fit score appears (ring + selector chip).
    await waitFor(() => expect(screen.getAllByText('72').length).toBeGreaterThan(0))
    // Section header (panel + readiness card both label it).
    expect(screen.getAllByText('Major-specific readiness').length).toBeGreaterThan(0)
    // Coach overlay — a suggested artifact.
    expect(screen.getByText(/Add a public GitHub/)).toBeTruthy()
    // The track form renders the catalog field label.
    expect(screen.getByText('Data structures & algorithms')).toBeTruthy()

    // Feedback-only: no generate / write-for-me / autofill control.
    const labels = screen.getAllByRole('button').map(b => (b.textContent ?? '').toLowerCase())
    expect(labels.some(t => /generate|write (my|your|for)|autofill|fill in/.test(t))).toBe(false)
  })
})
