import { describe, expect, it } from 'vitest'

import { stripToolCalls } from '../pages/student/discover/sanitize'

describe('stripToolCalls', () => {
  it('removes a backtick-wrapped suggest_replies tool call', () => {
    const input =
      'Where are you based?\n\n`suggest_replies(options=["Southern California", "Midwest, small town"])`'
    expect(stripToolCalls(input)).toBe('Where are you based?')
  })

  it('removes record_artifact / request_layer_advance leaks', () => {
    expect(stripToolCalls('Got it. record_artifact(type="x")')).toBe('Got it.')
    expect(stripToolCalls('Nice. request_layer_advance(rationale="done")')).toBe('Nice.')
  })

  it('leaves clean counselor prose untouched', () => {
    expect(stripToolCalls('Tell me about your goals.')).toBe('Tell me about your goals.')
  })

  it('handles empty input', () => {
    expect(stripToolCalls('')).toBe('')
  })
})
