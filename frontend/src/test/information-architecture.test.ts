import { describe, expect, it } from 'vitest'
import {
  PROFILE_TABS_SPEC,
  PROFILE_TAB_ALIASES,
  STUDENT_LEGACY_REDIRECTS,
  MANAGE_TAB_REDIRECTS,
  normalizeProfileTab,
} from '../utils/information-architecture'
import { postLoginDestination, roleDefaultPath, resolveNextParam } from '../utils/auth-redirect'

/** Spec/04 compliance — route contract tests. */
describe('Spec/04 information architecture', () => {
  it('defines 13 profile tabs per §4.6', () => {
    expect(PROFILE_TABS_SPEC).toHaveLength(13)
    expect(PROFILE_TABS_SPEC[0]).toBe('overview')
    expect(PROFILE_TABS_SPEC).toContain('preparation')
    expect(PROFILE_TABS_SPEC).toContain('analytics')
    expect(PROFILE_TABS_SPEC).toContain('data')
  })

  it('maps legacy profile tab aliases', () => {
    expect(PROFILE_TAB_ALIASES.essays).toBe('/s/prep?tab=workshops')
    expect(PROFILE_TAB_ALIASES.recommenders).toContain('tab=preparation')
  })

  it('normalizes deprecated tab keys', () => {
    expect(normalizeProfileTab('recommenders')).toBe('preparation')
    expect(normalizeProfileTab(null)).toBe('overview')
    expect(normalizeProfileTab('academics')).toBe('academics')
  })

  it('lists student legacy redirects from §4.4', () => {
    expect(STUDENT_LEGACY_REDIRECTS['/s/discover']).toBe('/s/explore')
    expect(STUDENT_LEGACY_REDIRECTS['/s/recommendations']).toContain('preparation')
    expect(STUDENT_LEGACY_REDIRECTS['/s/test-scores']).toBe('/s/profile?tab=academics')
  })

  // My Space (Spec 2026-06-10 §2) — /s/manage retired; rooms are real routes.
  it('retires /s/manage into My Space rooms', () => {
    expect(STUDENT_LEGACY_REDIRECTS['/s/manage']).toBe('/s/space')
    expect(STUDENT_LEGACY_REDIRECTS['/s/dashboard']).toBe('/s/space')
    expect(STUDENT_LEGACY_REDIRECTS['/s/deadlines']).toBe('/s/calendar')
    expect(STUDENT_LEGACY_REDIRECTS['/s/decisions']).toBe('/s/applications')
    expect(STUDENT_LEGACY_REDIRECTS['/s/essay-workshop']).toBe('/s/prep?tab=workshops')
    // Rooms resurrected as first-class routes — they must NOT be redirects.
    for (const room of ['/s/applications', '/s/calendar', '/s/messages', '/s/saved', '/s/profile', '/s/space', '/s/prep']) {
      expect(STUDENT_LEGACY_REDIRECTS[room]).toBeUndefined()
    }
    // Tab deep links keep working, one hop, param-preserving (ManageRedirect).
    expect(MANAGE_TAB_REDIRECTS.applications).toBe('/s/applications')
    expect(MANAGE_TAB_REDIRECTS.calendar).toBe('/s/calendar')
    expect(MANAGE_TAB_REDIRECTS.messages).toBe('/s/messages')
    expect(MANAGE_TAB_REDIRECTS.prompts).toBe('/s/prep?tab=prompts')
    expect(MANAGE_TAB_REDIRECTS.workshops).toBe('/s/prep?tab=workshops')
    // No redirect target may itself be a legacy path (no chains).
    for (const target of [...Object.values(STUDENT_LEGACY_REDIRECTS), ...Object.values(MANAGE_TAB_REDIRECTS)]) {
      expect(STUDENT_LEGACY_REDIRECTS[target.split('?')[0]]).toBeUndefined()
    }
  })

  it('uses role-default landing paths from §9', () => {
    expect(roleDefaultPath('student')).toBe('/s')
    expect(roleDefaultPath('institution_admin')).toBe('/i/dashboard')
  })

  it('honors safe ?next= redirects after login', () => {
    const params = new URLSearchParams('next=/s/saved')
    expect(postLoginDestination('student', params)).toBe('/s/saved')
    expect(postLoginDestination('student', new URLSearchParams('next=//evil.com'))).toBe('/s')
    expect(resolveNextParam('/s/explore?compare=open', '/s')).toBe('/s/explore?compare=open')
  })
})
