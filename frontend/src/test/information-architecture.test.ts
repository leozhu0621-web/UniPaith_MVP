import { describe, expect, it } from 'vitest'
import {
  PROFILE_TABS_SPEC,
  PROFILE_TAB_ALIASES,
  STUDENT_LEGACY_REDIRECTS,
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
    expect(PROFILE_TAB_ALIASES.essays).toBe('/s/manage?tab=workshops')
    expect(PROFILE_TAB_ALIASES.recommenders).toContain('tab=preparation')
  })

  it('normalizes deprecated tab keys', () => {
    expect(normalizeProfileTab('recommenders')).toBe('preparation')
    expect(normalizeProfileTab(null)).toBe('overview')
    expect(normalizeProfileTab('academics')).toBe('academics')
  })

  it('lists student legacy redirects from §4.4', () => {
    expect(STUDENT_LEGACY_REDIRECTS['/s/discover']).toBe('/s/explore')
    expect(STUDENT_LEGACY_REDIRECTS['/s/messages']).toBe('/s/manage?tab=messages')
    expect(STUDENT_LEGACY_REDIRECTS['/s/recommendations']).toContain('preparation')
    expect(STUDENT_LEGACY_REDIRECTS['/s/test-scores']).toBe('/s/profile?tab=academics')
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
