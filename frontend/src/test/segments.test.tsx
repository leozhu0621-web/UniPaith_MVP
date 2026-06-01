/**
 * Spec 26 — Audience Segmentation builder tests.
 *
 *   - The list renders saved segments with plain-language rule chips (§4).
 *   - "New segment" opens the rule-tree builder with Include/Exclude branches
 *     and the AI-assist bar (§3/§6).
 *   - Editing a segment + "Preview audience" surfaces the audience count (§3).
 */
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { MemoryRouter, Routes, Route } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { describe, expect, it, vi, beforeEach } from 'vitest'

const h = vi.hoisted(() => ({
  previewMock: vi.fn(),
  segment: {
    id: 'seg-1',
    institution_id: 'inst-1',
    program_id: null,
    segment_name: 'High-fit prospects',
    description: 'Strong matches worth nurturing',
    rules: {
      include: {
        op: 'AND',
        rules: [{ field: 'fit_band', operator: 'in', value: ['high'], branch: 'include' }],
      },
      exclude: { op: 'AND', rules: [] },
    },
    criteria: null,
    uploaded_list_ids: [],
    frequency_cap_per_week: null,
    preview_audience_count: 42,
    is_active: true,
    created_at: '2026-05-31T00:00:00Z',
    updated_at: '2026-05-31T00:00:00Z',
  },
  dictionary: {
    categories: [
      { key: 'fit', label: 'Fit & likelihood' },
      { key: 'activity', label: 'Platform activity' },
    ],
    signals: [
      {
        key: 'fit_band',
        label: 'Fit-to-program band',
        category: 'fit',
        category_label: 'Fit & likelihood',
        operators: ['in'],
        value_type: 'band',
        options: [
          { value: 'high', label: 'High' },
          { value: 'medium', label: 'Medium' },
          { value: 'low', label: 'Low' },
        ],
        plain_language: 'Fit band is {value}',
        protected: false,
        derived: false,
        help_text: '',
      },
      {
        key: 'saved_program',
        label: 'Saved any of our programs',
        category: 'activity',
        category_label: 'Platform activity',
        operators: ['exists'],
        value_type: 'boolean',
        options: null,
        plain_language: 'Saved one of our programs',
        protected: false,
        derived: false,
        help_text: '',
      },
    ],
  },
}))

vi.mock('../api/institutions', () => ({
  getSegments: vi.fn().mockResolvedValue([h.segment]),
  getInstitutionPrograms: vi.fn().mockResolvedValue([]),
  getSegmentSignalDictionary: vi.fn().mockResolvedValue(h.dictionary),
  previewSegmentRules: (...a: unknown[]) => h.previewMock(...a),
  createSegment: vi.fn().mockResolvedValue(h.segment),
  updateSegment: vi.fn().mockResolvedValue(h.segment),
  deleteSegment: vi.fn().mockResolvedValue(undefined),
  segmentNlBridge: vi
    .fn()
    .mockResolvedValue({ rules: [], confidence_overall: 0, ambiguity_notes: [] }),
}))
vi.mock('../stores/toast-store', () => ({ showToast: vi.fn() }))

import SegmentsPage from '../pages/institution/SegmentsPage'

function renderPage() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter initialEntries={['/i/segments']}>
        <Routes>
          <Route path="/i/segments" element={<SegmentsPage />} />
          <Route path="/i/outreach" element={<div>Campaigns</div>} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

beforeEach(() => {
  h.previewMock.mockReset()
})

describe('Spec 26 — audience segmentation', () => {
  it('renders saved segments with a plain-language rule chip', async () => {
    renderPage()
    expect(await screen.findByText('High-fit prospects')).toBeInTheDocument()
    // plain-language rendering of the fit_band=high rule (§4)
    expect(await screen.findByText('Fit band is High')).toBeInTheDocument()
    // cached audience count surfaced
    expect(screen.getByText('~42 students')).toBeInTheDocument()
  })

  it('opens the builder with Include/Exclude branches and AI assist', async () => {
    renderPage()
    fireEvent.click(await screen.findByText('New segment'))
    expect(await screen.findByText('Include')).toBeInTheDocument()
    expect(screen.getByText('Exclude')).toBeInTheDocument()
    expect(screen.getByText(/Try AI assist/i)).toBeInTheDocument()
    expect(screen.getByText('Save segment')).toBeInTheDocument()
  })

  it('previews the audience for an edited segment', async () => {
    h.previewMock.mockResolvedValue({
      audience_count: 42,
      platform_count: 42,
      uploaded_external_count: 0,
      sample: [
        {
          student_id: 's1',
          name: 'Ada L.',
          email: null,
          nationality: 'USA',
          country_of_residence: null,
          fit_band: 'high',
        },
      ],
      composition: {},
      fairness_warning: null,
    })
    renderPage()
    fireEvent.click((await screen.findAllByText('Edit'))[0])
    fireEvent.click(await screen.findByRole('button', { name: 'Preview audience' }))
    await waitFor(() => expect(h.previewMock).toHaveBeenCalled())
    expect(await screen.findByText('42')).toBeInTheDocument()
    expect(await screen.findByText('Ada L.')).toBeInTheDocument()
  })

  it('surfaces a fairness warning when the audience skews', async () => {
    h.previewMock.mockResolvedValue({
      audience_count: 30,
      platform_count: 30,
      uploaded_external_count: 0,
      sample: [],
      composition: { nationality: { USA: 28, India: 2 } },
      fairness_warning:
        'This audience skews heavily on nationality (93% USA). Review for fairness before sending.',
    })
    renderPage()
    fireEvent.click((await screen.findAllByText('Edit'))[0])
    fireEvent.click(await screen.findByRole('button', { name: 'Preview audience' }))
    expect(await screen.findByText(/skews heavily on nationality/i)).toBeInTheDocument()
  })
})
