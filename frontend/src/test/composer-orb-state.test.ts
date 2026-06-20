import { describe, it, expect } from 'vitest'

import { deriveComposerOrbState } from '../pages/student/discover/composerOrbState'

const base = {
  streaming: false,
  streamText: '',
  pending: false,
  draft: '',
  celebrating: false,
}

describe('deriveComposerOrbState', () => {
  it('is idle at rest', () => {
    expect(deriveComposerOrbState(base)).toBe('idle')
  })

  it('listens while the student is composing', () => {
    expect(deriveComposerOrbState({ ...base, draft: 'I am a junior' })).toBe('listening')
    // whitespace-only draft is not composing
    expect(deriveComposerOrbState({ ...base, draft: '   ' })).toBe('idle')
  })

  it('thinks while awaiting a reply', () => {
    expect(deriveComposerOrbState({ ...base, pending: true })).toBe('thinking')
    // streaming opened but no text yet = still thinking
    expect(deriveComposerOrbState({ ...base, streaming: true, streamText: '' })).toBe('thinking')
  })

  it('responds while the reply streams in', () => {
    expect(
      deriveComposerOrbState({ ...base, streaming: true, streamText: 'Hello' }),
    ).toBe('responding')
  })

  it('celebrates a milestone, but activity outranks it', () => {
    expect(deriveComposerOrbState({ ...base, celebrating: true })).toBe('celebrating')
    // a live reply takes priority over the celebrate flag
    expect(
      deriveComposerOrbState({
        ...base,
        celebrating: true,
        streaming: true,
        streamText: 'x',
      }),
    ).toBe('responding')
  })

  it('priority: responding > thinking > celebrating > listening > idle', () => {
    // typing while a reply streams → responding (not listening)
    expect(
      deriveComposerOrbState({ ...base, draft: 'typing', streaming: true, streamText: 'x' }),
    ).toBe('responding')
    // typing while pending → thinking (not listening)
    expect(deriveComposerOrbState({ ...base, draft: 'typing', pending: true })).toBe('thinking')
    // celebrating while typing → celebrating (not listening)
    expect(deriveComposerOrbState({ ...base, draft: 'typing', celebrating: true })).toBe(
      'celebrating',
    )
  })
})
