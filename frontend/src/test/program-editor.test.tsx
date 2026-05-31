/**
 * Spec 23 — Program editor (institution-facing) tests.
 *
 *   - The guided editor renders all 8 sections (G-I1: no raw-JSON-only blobs).
 *   - Guided repeatable lists add rows (e.g. application materials).
 *   - Publish validation surfaces a modal listing each missing field with a
 *     jump-to-section link (§6).
 */
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { MemoryRouter, Routes, Route } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { describe, expect, it, vi, beforeEach } from 'vitest'

const h = vi.hoisted(() => ({
  createMock: vi.fn(),
  updateMock: vi.fn(),
  publishMock: vi.fn(),
  editProgram: {
    id: 'p1',
    institution_id: 'inst-1',
    school_id: null,
    program_name: 'Computer Science, M.S.',
    degree_type: 'masters',
    department: 'Engineering',
    duration_months: 24,
    tuition: null,
    acceptance_rate: null,
    delivery_format: 'in_person',
    campus_setting: 'urban',
    requirements: null,
    application_requirements: { materials: [], prerequisites: [], test_policy: { stance: 'test_optional', required: [], optional: [], accepted_tests: [], superscore_enabled: false, waived_rules: '', typical_ranges: [] }, recommendations: { required_count: 0, types: [] } },
    description_text: '',
    who_its_for: '',
    is_published: false,
    status: 'draft',
    version: 1,
    feature_version: 1,
    applications_count: 0,
    application_deadline: null,
    program_start_date: null,
    tracks: null,
    outcomes_data: {},
    intake_rounds: [],
    media_urls: [],
    highlights: [],
    faculty_contacts: [],
    cost_data: {},
    promotion_categories: [],
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
  },
}))

const editProgram = h.editProgram

vi.mock('../api/institutions', () => ({
  getInstitution: vi.fn().mockResolvedValue({ id: 'inst-1', name: 'Test University' }),
  getInstitutionSchools: vi.fn().mockResolvedValue([{ id: 's1', name: 'School of Engineering' }]),
  getInstitutionProgram: vi.fn().mockResolvedValue(h.editProgram),
  createProgram: (...a: unknown[]) => h.createMock(...a),
  updateProgram: (...a: unknown[]) => h.updateMock(...a),
  publishProgram: (...a: unknown[]) => h.publishMock(...a),
  unpublishProgram: vi.fn().mockResolvedValue(h.editProgram),
}))
vi.mock('../stores/toast-store', () => ({ showToast: vi.fn() }))

import ProgramEditorPage from '../pages/institution/ProgramEditorPage'

function renderEditor(initial: string) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter initialEntries={[initial]}>
        <Routes>
          <Route path="/i/programs/new" element={<ProgramEditorPage />} />
          <Route path="/i/programs/:id/edit" element={<ProgramEditorPage />} />
          <Route path="/i/programs" element={<div>Programs list</div>} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

const SECTION_TITLES = [
  'Identity',
  'Overview & structure',
  'Requirements',
  'Deadlines & rounds',
  'Costs',
  'Outcomes',
  'Media',
  'Promotion settings',
]

beforeEach(() => {
  h.createMock.mockReset()
  h.updateMock.mockReset()
  h.publishMock.mockReset()
  // jsdom doesn't implement scrollIntoView — stub it for goToSection.
  Element.prototype.scrollIntoView = vi.fn()
})

describe('Spec 23 — program editor', () => {
  it('renders all 8 guided sections for a new program', () => {
    renderEditor('/i/programs/new')
    for (const title of SECTION_TITLES) {
      expect(screen.getAllByText(title).length).toBeGreaterThan(0)
    }
    expect(screen.getByText('Publish program')).toBeInTheDocument()
    expect(screen.getByText('Save draft')).toBeInTheDocument()
  })

  it('adds a guided application-material row (no raw JSON required)', async () => {
    renderEditor('/i/programs/new')
    expect(screen.queryByPlaceholderText('e.g. Statement of purpose')).not.toBeInTheDocument()
    fireEvent.click(screen.getByText('Add material'))
    expect(await screen.findByPlaceholderText('e.g. Statement of purpose')).toBeInTheDocument()
  })

  it('exposes an Advanced (raw JSON) escape hatch on structured sections', () => {
    renderEditor('/i/programs/new')
    // Costs / Outcomes / Requirements / Deadlines each carry the toggle.
    expect(screen.getAllByText('Advanced (raw JSON)').length).toBeGreaterThanOrEqual(4)
  })

  it('shows a validation modal listing missing fields with jump-to-section links', async () => {
    h.updateMock.mockResolvedValue({ ...editProgram, version: 2, feature_version: 2 })
    h.publishMock.mockRejectedValue({
      response: {
        status: 422,
        data: {
          detail: {
            message: 'This program is missing required fields. Resolve to publish.',
            missing_fields: [
              { field: 'description_text', section: 'overview', message: 'A program description is required.' },
            ],
          },
        },
      },
    })

    renderEditor('/i/programs/p1/edit')
    // Wait for the program to load (header shows its name).
    await screen.findByText('Computer Science, M.S.')

    fireEvent.click(screen.getByText('Publish program'))

    const dialog = await screen.findByText('This program is missing required fields. Resolve to publish.')
    expect(dialog).toBeInTheDocument()
    expect(screen.getByText('A program description is required.')).toBeInTheDocument()

    const jump = screen.getByText('Go to Overview & structure →')
    fireEvent.click(jump)
    // Clicking the jump link dismisses the modal and scrolls to the section.
    await waitFor(() =>
      expect(
        screen.queryByText('This program is missing required fields. Resolve to publish.'),
      ).not.toBeInTheDocument(),
    )
    expect(Element.prototype.scrollIntoView).toHaveBeenCalled()
  })
})
