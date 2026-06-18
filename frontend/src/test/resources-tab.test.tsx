// Discover Resources tab (Spec 2026-06-14) — content guides + readiness panel +
// sub-tab bar. Verifies the authored guides are non-empty and the readiness
// panel reads ONLY real fields (✓ vs "Add in Profile"), never a guessed value.
import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent, within } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

import { AID_GUIDE, AID_GUIDE_DISCLAIMER } from '../pages/student/explore/resources/aidGuide'
import { INTL_GUIDE, INTL_GUIDE_DISCLAIMER } from '../pages/student/explore/resources/intlGuide'
import ResourcesTabBar, { normalizeSub, RESOURCES_SUBS } from '../pages/student/explore/resources/ResourcesTabBar'

vi.mock('../api/students', () => ({ getVisaInfo: vi.fn(), listTestScores: vi.fn() }))
import { getVisaInfo, listTestScores } from '../api/students'
import ReadinessPanel from '../pages/student/explore/resources/ReadinessPanel'

describe('authored guides are complete and disclaimered', () => {
  it('financial guide has sections, each with a heading + body', () => {
    expect(AID_GUIDE.length).toBeGreaterThanOrEqual(4)
    for (const s of AID_GUIDE) {
      expect(s.heading.length).toBeGreaterThan(0)
      expect(s.body.length).toBeGreaterThan(0)
    }
    expect(AID_GUIDE_DISCLAIMER).toMatch(/confirm/i)
  })
  it('international guide has sections + visa/OPT/English topics', () => {
    expect(INTL_GUIDE.length).toBeGreaterThanOrEqual(5)
    const headings = INTL_GUIDE.map(s => s.heading.toLowerCase()).join(' ')
    expect(headings).toMatch(/visa/)
    expect(headings).toMatch(/english/)
    expect(INTL_GUIDE_DISCLAIMER).toMatch(/official|confirm/i)
  })
})

describe('ResourcesTabBar', () => {
  it('normalizes an unknown sub to universities', () => {
    expect(normalizeSub(null)).toBe('universities')
    expect(normalizeSub('garbage')).toBe('universities')
    expect(normalizeSub('financial')).toBe('financial')
  })
  it('renders all three sub-tabs and fires onChange', () => {
    const onChange = vi.fn()
    render(<ResourcesTabBar sub="universities" onChange={onChange} />)
    const list = screen.getByRole('tablist', { name: 'Resources sections' })
    for (const label of ['Universities', 'Financial', 'International']) {
      expect(within(list).getByText(label)).toBeTruthy()
    }
    fireEvent.click(screen.getByText('Financial'))
    expect(onChange).toHaveBeenCalledWith('financial')
  })
  it('exposes the three canonical subs', () => {
    expect([...RESOURCES_SUBS]).toEqual(['universities', 'financial', 'international'])
  })
})

function renderReadiness() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={qc}><MemoryRouter><ReadinessPanel /></MemoryRouter></QueryClientProvider>,
  )
}

describe('ReadinessPanel reads only real fields', () => {
  it('shows a present field as done and a missing one as an Add prompt', async () => {
    vi.mocked(getVisaInfo).mockResolvedValue({
      visa_required: true,
      target_study_country: 'United States',
      current_immigration_status: null,
      financial_proof_available: false,
      passport_expiration_date: null,
    } as never)
    vi.mocked(listTestScores).mockResolvedValue([{ test_type: 'IELTS', total_score: 7.5 }] as never)
    renderReadiness()
    expect(await screen.findByText('United States')).toBeTruthy() // present field value
    expect(screen.getByText('IELTS 7.5 on file')).toBeTruthy() // real test_type + total_score
    expect(screen.getAllByText('Add in Profile →').length).toBeGreaterThan(0) // a missing field prompts
  })

  it('collapses for a student who does not need a visa', async () => {
    vi.mocked(getVisaInfo).mockResolvedValue({ visa_required: false } as never)
    vi.mocked(listTestScores).mockResolvedValue([] as never)
    renderReadiness()
    expect(await screen.findByText(/don’t need a study visa/i)).toBeTruthy()
  })
})
