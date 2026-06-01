import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter } from 'react-router-dom'
import SettingsPage from '../pages/institution/SettingsPage'
import * as institutionsApi from '../api/institutions'
import * as reviewsApi from '../api/reviews'
import * as settingsApi from '../api/settings'
import * as billingApi from '../api/billing'
import * as notificationsApi from '../api/notifications'

const INSTITUTION_SETTINGS = {
  account: {
    institution_id: 'inst-1',
    name: 'University of Foo',
    contact_email: 'admissions@foo.edu',
    website_url: 'https://www.foo.edu',
    primary_domain: 'foo.edu',
    member_since: '2026-01-01T00:00:00Z',
  },
  security: { mfa_enabled: false, mfa_method: null },
  preferences: {
    locale: 'en',
    timezone: 'UTC',
    theme: 'system',
    accessibility: { dyslexia_mode: false, font_size: 'md', reduced_motion: false },
  },
  notifications: [],
  email_enabled: true,
  email_frequency: 'all',
  team: [],
  deletion: null,
  review_config: {
    blind_review_default: false,
    calibration_enabled: true,
    reviewer_assignment_mode: 'round_robin',
  },
}

// Spec 22 §3 / gap G-I1 — the institution profile editor uses guided forms,
// not raw JSON. These tests prove the round-trip: load the JSONB dicts into
// labelled rows, edit a row, and save a correctly-shaped payload — while
// preserving keys/shapes the widgets don't model (lossless).

const INSTITUTION = {
  id: 'inst-1',
  admin_user_id: 'u-1',
  name: 'University of Foo',
  type: 'university',
  country: 'USA',
  region: 'NY',
  city: 'New York',
  founded_year: 1831,
  updated_at: '2026-01-01T00:00:00Z',
  social_links: { twitter: 'https://x.com/foo' },
  inquiry_routing: { general: 'admissions@foo.edu' },
  support_services: { tutoring: { name: 'Tutoring', url: 'https://foo.edu/tutoring' } },
  policies: { transfer_credit: { summary: 'We accept up to 60 credits.', url: 'https://foo.edu/transfer' } },
  international_info: { toefl_min: 100, supported_visas: ['F-1', 'J-1'], visa_contact: 'ogs@foo.edu' },
  // `nested_unknown` is an object value the metric editor can't model as a row —
  // it must survive a save untouched (preservation).
  school_outcomes: { employed_or_continuing_ed: 0.94, top_employers: ['Google'], nested_unknown: { a: 1 } },
  media_gallery: [],
}

function mockApis() {
  vi.spyOn(institutionsApi, 'getInstitution').mockResolvedValue(INSTITUTION as any)
  vi.spyOn(institutionsApi, 'updateInstitution').mockResolvedValue(INSTITUTION as any)
  vi.spyOn(reviewsApi, 'getRubrics').mockResolvedValue([] as any)
  vi.spyOn(billingApi, 'getInstitutionBilling').mockResolvedValue({} as any)
  vi.spyOn(settingsApi, 'getInstitutionSettings').mockResolvedValue(INSTITUTION_SETTINGS as any)
  vi.spyOn(notificationsApi, 'getNotificationPrefs').mockResolvedValue({ email_enabled: true, preferences: {} } as any)
}

async function openProfileTab() {
  fireEvent.click(screen.getByRole('tab', { name: /public profile/i }))
  expect(await screen.findByDisplayValue('University of Foo')).toBeInTheDocument()
}

function renderSettings() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <SettingsPage />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

beforeEach(() => {
  vi.restoreAllMocks()
  mockApis()
})

describe('Institution SettingsPage — guided profile editors (Spec 22 G-I1)', () => {
  it('decomposes the JSONB dicts into labelled rows (no raw JSON textarea)', async () => {
    renderSettings()
    await openProfileTab()
    // support_services → name + url rows
    expect(screen.getByDisplayValue('Tutoring')).toBeInTheDocument()
    expect(screen.getByDisplayValue('https://foo.edu/tutoring')).toBeInTheDocument()
    // policies (withSummary) → summary textarea
    expect(screen.getByDisplayValue('We accept up to 60 credits.')).toBeInTheDocument()
    // international_info → scalar + list (rendered comma-joined)
    expect(screen.getByDisplayValue('F-1, J-1')).toBeInTheDocument()
    // school_outcomes → number metric
    expect(screen.getByDisplayValue('0.94')).toBeInTheDocument()
    // social_links + inquiry_routing pairs
    expect(screen.getByDisplayValue('https://x.com/foo')).toBeInTheDocument()
    expect(screen.getByDisplayValue('admissions@foo.edu')).toBeInTheDocument()
    // No raw JSON braces leaking into any field
    expect(screen.queryByDisplayValue(/^\{/)).not.toBeInTheDocument()
  })

  it('saves correctly-shaped dicts; edited fields re-slug, untouched fields and unknown keys are preserved', async () => {
    const updateSpy = vi.spyOn(institutionsApi, 'updateInstitution')
    renderSettings()
    await openProfileTab()

    // Edit a support-service name → key must re-slug, url carried along.
    fireEvent.change(screen.getByDisplayValue('Tutoring'), { target: { value: 'Peer Tutoring' } })
    // Edit an outcome number → its editor emits, must keep the preserved object.
    fireEvent.change(screen.getByDisplayValue('0.94'), { target: { value: '0.96' } })

    fireEvent.click(screen.getByRole('button', { name: /save changes/i }))

    await waitFor(() => expect(updateSpy).toHaveBeenCalled())
    const payload: any = updateSpy.mock.calls[0][0]

    // Edited support service: re-slugged key, name updated, url preserved.
    expect(payload.support_services).toEqual({
      peer_tutoring: { name: 'Peer Tutoring', url: 'https://foo.edu/tutoring' },
    })
    // Edited outcomes: number stays a number, list + unknown object preserved.
    expect(payload.school_outcomes.employed_or_continuing_ed).toBe(0.96)
    expect(payload.school_outcomes.top_employers).toEqual(['Google'])
    expect(payload.school_outcomes.nested_unknown).toEqual({ a: 1 })
    // Untouched fields go out exactly as loaded.
    expect(payload.policies).toEqual(INSTITUTION.policies)
    expect(payload.social_links).toEqual({ twitter: 'https://x.com/foo' })
    expect(payload.inquiry_routing).toEqual({ general: 'admissions@foo.edu' })
    expect(payload.international_info.supported_visas).toEqual(['F-1', 'J-1'])
    expect(payload.international_info.toefl_min).toBe(100)
  })

  it('lets an admin add a new social link row that ends up in the payload', async () => {
    const updateSpy = vi.spyOn(institutionsApi, 'updateInstitution')
    renderSettings()
    await openProfileTab()

    fireEvent.click(screen.getByRole('button', { name: /add social link/i }))
    // The new empty row exposes a Platform + URL input pair; fill them.
    const platformInputs = screen.getAllByPlaceholderText('Platform')
    const urlInputs = screen.getAllByPlaceholderText('https://…')
    fireEvent.change(platformInputs[platformInputs.length - 1], { target: { value: 'linkedin' } })
    fireEvent.change(urlInputs[urlInputs.length - 1], { target: { value: 'https://linkedin.com/school/foo' } })

    fireEvent.click(screen.getByRole('button', { name: /save changes/i }))
    await waitFor(() => expect(updateSpy).toHaveBeenCalled())
    const payload: any = updateSpy.mock.calls[0][0]
    expect(payload.social_links).toEqual({
      twitter: 'https://x.com/foo',
      linkedin: 'https://linkedin.com/school/foo',
    })
  })
})
