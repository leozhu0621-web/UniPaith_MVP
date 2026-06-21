// Academic › Universities Programs/Universities toggle (Discover review
// 2026-06-19 #3). Pins the mode contract: explicit ?umode= wins; otherwise the
// default follows the URL so a shared program-search deep-link opens Programs.
import { describe, it, expect } from 'vitest'
import { resolveBrowseMode } from '../pages/student/explore/browseMode'

describe('resolveBrowseMode', () => {
  it('honors an explicit ?umode=', () => {
    expect(resolveBrowseMode('programs', false)).toBe('programs')
    expect(resolveBrowseMode('universities', true)).toBe('universities')
  })

  it('defaults to Programs when a program search is active (shared deep-link)', () => {
    expect(resolveBrowseMode(null, true)).toBe('programs')
  })

  it('defaults to Universities otherwise — matching the sub-tab name', () => {
    expect(resolveBrowseMode(null, false)).toBe('universities')
  })

  it('ignores a bogus umode value and falls back to the default', () => {
    expect(resolveBrowseMode('garbage', false)).toBe('universities')
    expect(resolveBrowseMode('', true)).toBe('programs')
  })
})
