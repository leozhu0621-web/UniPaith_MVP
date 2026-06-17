import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

import PreferencesTab from '../pages/student/profile/PreferencesTab'
import * as studentsApi from '../api/students'

// The six matcher inputs that used to be free text are now canonical controls.
// These tests pin (a) that they render as Selects / chips, and (b) the
// save round-trip — countries stay a string[], degree level a catalog value.

function renderTab() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={qc}>
      <PreferencesTab />
    </QueryClientProvider>,
  )
}

describe('PreferencesTab — canonical controls', () => {
  beforeEach(() => vi.restoreAllMocks())

  it('renders degree level / start term / climate / program style as selects, not text inputs', async () => {
    vi.spyOn(studentsApi, 'getPreferences').mockResolvedValue({})
    renderTab()

    const degree = (await screen.findByLabelText('Target degree level')) as HTMLElement
    expect(degree.tagName).toBe('SELECT')
    expect(degree.querySelector('option[value="masters"]')).not.toBeNull()

    const term = screen.getByLabelText('Target start term') as HTMLElement
    expect(term.tagName).toBe('SELECT')

    const climate = screen.getByLabelText('Climate') as HTMLElement
    expect(climate.tagName).toBe('SELECT')
    expect(climate.querySelector('option[value="four_seasons"]')).not.toBeNull()

    const style = screen.getByLabelText('Program style') as HTMLElement
    expect(style.tagName).toBe('SELECT')
    expect(style.querySelector('option[value="research"]')).not.toBeNull()
  })

  it('renders preferred countries / regions as chip toggles seeded from the geo catalog', async () => {
    vi.spyOn(studentsApi, 'getPreferences').mockResolvedValue({})
    renderTab()

    const countries = await screen.findByRole('group', { name: 'Preferred countries' })
    expect(countries.querySelector('button')).not.toBeNull()
    // A representative catalog chip is offered; the guided-only "Anywhere" is not.
    expect(within(countries).getByRole('button', { name: /United States/ })).toBeInTheDocument()
    expect(within(countries).queryByRole('button', { name: /^Anywhere/ })).toBeNull()

    expect(screen.getByRole('group', { name: 'Preferred regions' })).toBeInTheDocument()
  })

  it('loads a saved country back into the chips as selected', async () => {
    vi.spyOn(studentsApi, 'getPreferences').mockResolvedValue({ preferred_countries: ['Canada'] })
    renderTab()

    const countries = await screen.findByRole('group', { name: 'Preferred countries' })
    const canada = within(countries).getByRole('button', { name: /Canada/ })
    expect(canada).toHaveAttribute('aria-pressed', 'true')
  })

  it('saves countries as a string[] and degree level as a catalog value', async () => {
    vi.spyOn(studentsApi, 'getPreferences').mockResolvedValue({})
    const upsert = vi.spyOn(studentsApi, 'upsertPreferences').mockResolvedValue({} as never)
    renderTab()

    const countries = await screen.findByRole('group', { name: 'Preferred countries' })
    fireEvent.click(within(countries).getByRole('button', { name: /United States/ }))

    fireEvent.change(screen.getByLabelText('Target degree level'), { target: { value: 'masters' } })

    fireEvent.click(screen.getByRole('button', { name: 'Save preferences' }))

    await waitFor(() => expect(upsert).toHaveBeenCalled())
    const payload = upsert.mock.calls[0][0] as Record<string, unknown>
    expect(payload.preferred_countries).toEqual(['United States'])
    expect(payload.target_degree_level).toBe('masters')
  })
})
