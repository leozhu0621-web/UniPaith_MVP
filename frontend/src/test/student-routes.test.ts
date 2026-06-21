import { describe, expect, it } from 'vitest'
import { resolveManageRedirect } from '../lib/student-routes'

function redirectFor(query: string) {
  return resolveManageRedirect(new URLSearchParams(query))
}

describe('student route contracts', () => {
  it('redirects retired manage routes to canonical My Space rooms', () => {
    expect(redirectFor('')).toBe('/s/space')
    expect(redirectFor('tab=applications&application=app-1')).toBe('/s/applications?application=app-1')
    expect(redirectFor('tab=calendar&view=week')).toBe('/s/calendar?view=week')
    expect(redirectFor('tab=messages&thread=thread-1')).toBe('/s/messages?thread=thread-1')
  })

  it('preserves params when redirecting nested Prep tabs', () => {
    expect(redirectFor('tab=workshops&application=app-1')).toBe('/s/prep?tab=workshops&application=app-1')
    expect(redirectFor('tab=prompts&return_to=%2Fs%2Fspace')).toBe('/s/prep?tab=prompts&return_to=%2Fs%2Fspace')
  })

  it('falls unknown manage tabs back to My Space without dropping context', () => {
    expect(redirectFor('tab=legacy&thread=thread-1')).toBe('/s/space?thread=thread-1')
  })
})
