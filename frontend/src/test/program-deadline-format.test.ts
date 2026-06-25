// Program-card deadline countdown consistency (deadline-math sweep 2026-06-21).
// deadlineInfo() used to compute "Xd left" with date-fns differenceInDays, which
// TRUNCATES — so a 2.5-day deadline read "2d left" on a card while the rest of the
// app (Applications, Calendar, DeadlinePill) used the canonical daysUntil (ceil)
// and said 3. Now it uses daysUntil, so the whole app agrees.
import { describe, it, expect } from 'vitest'
import { deadlineInfo, degreeAbbrev } from '../pages/student/explore/cards/programFormat'

const inDays = (d: number) => new Date(Date.now() + d * 86_400_000).toISOString()

describe('deadlineInfo — canonical daysUntil countdown', () => {
  it('ceils partial days like the rest of the app (2.5d → "3d left", not "2d")', () => {
    const info = deadlineInfo(inDays(2.5))!
    expect(info.text).toBe('3d left')
    expect(info.urgent).toBe(true)
    expect(info.closed).toBe(false)
  })

  it('marks a past deadline closed (date shown, not urgent)', () => {
    const info = deadlineInfo(inDays(-3))!
    expect(info.closed).toBe(true)
    expect(info.urgent).toBe(false)
  })

  it('drives `urgent` (amber) by the canonical 7/21 tone, not the 30-day text window', () => {
    // 25 days: still shows the countdown (≤30 window) but is NOT urgent/amber — it
    // is amber on no surface that uses the canonical tone, so it must not be here.
    const far = deadlineInfo(inDays(25))!
    expect(far.text).toBe('25d left')
    expect(far.urgent).toBe(false)
    // 15 days: within the 21-day canonical warning band → urgent.
    expect(deadlineInfo(inDays(15))!.urgent).toBe(true)
  })

  it('shows the date (not a relative pill) beyond 30 days', () => {
    const info = deadlineInfo(inDays(45))!
    expect(info.closed).toBe(false)
    expect(info.urgent).toBe(false)
    expect(info.text).not.toMatch(/left/)
  })

  it('returns null when there is no deadline', () => {
    expect(deadlineInfo(null)).toBeNull()
  })

  it('renders a date-only deadline label via parseISO (local) so the card matches the detail page', () => {
    // Old `new Date("2099-03-15")` parsed as UTC midnight then rendered local,
    // rolling back to "Mar 14" west of UTC while the detail page showed "Mar 15".
    // parseISO keeps it local midnight → "Mar 15" in every timezone.
    expect(deadlineInfo('2099-03-15')!.text).toBe('Mar 15')
  })
})

describe('degreeAbbrev — title-aware monogram', () => {
  it('distinguishes BA from BS by the program title (not a blanket "BS")', () => {
    expect(degreeAbbrev('bachelors', 'Bachelor of Arts in English')).toBe('BA')
    expect(degreeAbbrev('bachelors', 'Bachelor of Science in Computer Science')).toBe('BS')
    // Ambiguous title → neutral monogram rather than the wrong "BS".
    expect(degreeAbbrev('bachelors', 'Computer Science')).toBe('BACH')
  })

  it('handles masters variants and passes other degrees through', () => {
    expect(degreeAbbrev('masters', 'Master of Business Administration')).toBe('MBA')
    expect(degreeAbbrev('masters', 'Master of Arts in History')).toBe('MA')
    expect(degreeAbbrev('phd', 'Doctor of Philosophy')).toBe('PhD')
  })
})
