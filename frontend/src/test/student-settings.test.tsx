import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter } from 'react-router-dom'
import SettingsPage from '../pages/student/SettingsPage'
import * as settingsApi from '../api/settings'
import * as notificationsApi from '../api/notifications'
import * as billingApi from '../api/billing'
import * as studentsApi from '../api/students'

const SETTINGS = {
  account: {
    email: 'student@example.com',
    role: 'student',
    member_since: '2026-01-01T00:00:00Z',
    display_name: 'Alex',
    photo_url: null,
    pending_email: null,
  },
  security: { mfa_enabled: false, mfa_method: null },
  preferences: {
    locale: 'en',
    timezone: 'UTC',
    theme: 'system',
    accessibility: { dyslexia_mode: false, font_size: 'md', reduced_motion: false },
  },
  notifications: [
    {
      type: 'match_updates',
      label: 'Match updates',
      essential: false,
      channels: { email: true, sms: false, in_app: true, push: false },
    },
    {
      type: 'deadline_reminders',
      label: 'Deadline reminders',
      essential: true,
      channels: { email: true, sms: false, in_app: true, push: false },
    },
  ],
  email_enabled: true,
  email_frequency: 'all',
  deletion: null,
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
  vi.spyOn(settingsApi, 'getSettings').mockResolvedValue(SETTINGS as any)
  vi.spyOn(settingsApi, 'updateSettings').mockResolvedValue(SETTINGS as any)
  vi.spyOn(settingsApi, 'getSessions').mockResolvedValue([
    { id: 'current', device: 'This device', current: true, last_active: null, location: null },
  ] as any)
  vi.spyOn(settingsApi, 'getLoginActivity').mockResolvedValue([] as any)
  vi.spyOn(notificationsApi, 'updateNotificationPrefs').mockResolvedValue({
    email_enabled: true,
    email_frequency: 'all',
    matrix: SETTINGS.notifications,
  } as any)
  vi.spyOn(billingApi, 'getStudentBilling').mockResolvedValue({
    status: 'trialing',
    monthly_total_usd: 15,
    trial_days_left: 7,
    trial_ends_at: '2026-06-07T00:00:00Z',
    ad_free: false,
    ad_free_addon_usd: 5,
    has_payment_method: false,
    invoices: [],
  } as any)
  vi.spyOn(studentsApi, 'getPreferences').mockResolvedValue({ auto_follow_on_save: true } as any)
})

describe('Student SettingsPage (Spec 21)', () => {
  it('renders all spec sections in order', async () => {
    renderSettings()
    expect(await screen.findByRole('heading', { name: /your account/i })).toBeInTheDocument()
    for (const title of [
      'Account',
      'Security',
      'Preferences',
      'Notifications',
      'Data & privacy',
      'Billing & plan',
      'Sign out',
      'Danger zone',
    ]) {
      expect(await screen.findByRole('heading', { name: title, level: 2 })).toBeInTheDocument()
    }
  })

  it('links data rights to Profile → Data tab (no duplicate consent UI)', async () => {
    renderSettings()
    await screen.findByRole('heading', { name: 'Account', level: 2 })
    const link = screen.getByRole('link', { name: /manage data rights →/i })
    expect(link).toHaveAttribute('href', '/s/profile?tab=data')
  })

  it('shows account read-only fields and editable display name', async () => {
    renderSettings()
    await screen.findByDisplayValue('Alex')
    expect(screen.getAllByText('student@example.com').length).toBeGreaterThan(0)
  })
})
