// ScrollReset policy (UX overhaul Ship A, 2026-06-12 spec §1):
// reset to top on PUSH/REPLACE (including ?tab= switches), restore the saved
// position on POP, and ALWAYS clear horizontal scroll. The #main scroll
// container persists across routes, so these tests mount a fake one.
import { test, expect, beforeEach, afterEach, vi } from 'vitest'
import { render, act, cleanup } from '@testing-library/react'
import { MemoryRouter, useNavigate } from 'react-router-dom'
import ScrollReset from '../components/layout/ScrollReset'

let navigateFn: ReturnType<typeof useNavigate>

function NavCapture() {
  navigateFn = useNavigate()
  return null
}

function renderAt(initialPath: string) {
  return render(
    <MemoryRouter initialEntries={[initialPath]}>
      <NavCapture />
      <ScrollReset />
    </MemoryRouter>,
  )
}

// jsdom implements neither element scroll metrics nor scrollTo — mock a
// scrollable #main whose scrollTo applies top/left like a real container.
function setupMain({ scrollHeight = 2000, clientHeight = 600 } = {}) {
  const main = document.createElement('div')
  main.id = 'main'
  Object.defineProperty(main, 'scrollHeight', { value: scrollHeight, configurable: true, writable: true })
  Object.defineProperty(main, 'clientHeight', { value: clientHeight, configurable: true, writable: true })
  main.scrollTo = vi.fn((options?: ScrollToOptions | number) => {
    if (typeof options === 'object' && options !== null) {
      if (options.top !== undefined) main.scrollTop = options.top
      if (options.left !== undefined) main.scrollLeft = options.left
    }
  }) as unknown as typeof main.scrollTo
  document.body.appendChild(main)
  return main
}

// The user scrolls: position changes AND a scroll event fires (the recorder
// listens for it).
function userScroll(main: HTMLElement, top: number) {
  main.scrollTop = top
  act(() => {
    main.dispatchEvent(new Event('scroll'))
  })
}

beforeEach(() => {
  sessionStorage.clear()
})

afterEach(() => {
  cleanup()
  document.getElementById('main')?.remove()
  vi.unstubAllGlobals()
})

test('PUSH resets scrollTop AND scrollLeft to 0', () => {
  const main = setupMain()
  renderAt('/a')

  main.scrollTop = 500
  main.scrollLeft = 120 // a too-wide child panned the shell
  act(() => navigateFn('/b'))

  expect(main.scrollTop).toBe(0)
  expect(main.scrollLeft).toBe(0)
})

test('POP restores the saved scrollTop and clears scrollLeft', () => {
  const main = setupMain()
  renderAt('/a')

  userScroll(main, 500)
  act(() => navigateFn('/b'))
  expect(main.scrollTop).toBe(0)

  main.scrollLeft = 80 // horizontal pan picked up on /b
  act(() => navigateFn(-1)) // back to /a

  expect(main.scrollTop).toBe(500)
  expect(main.scrollLeft).toBe(0)
})

test('search-param change (?tab=) resets scroll on PUSH', () => {
  const main = setupMain()
  renderAt('/s/explore')

  userScroll(main, 420)
  main.scrollLeft = 60
  act(() => navigateFn('/s/explore?tab=updates'))

  expect(main.scrollTop).toBe(0)
  expect(main.scrollLeft).toBe(0)
})

test('REPLACE resets scroll to top', () => {
  const main = setupMain()
  renderAt('/a')

  userScroll(main, 300)
  act(() => navigateFn('/b', { replace: true }))

  expect(main.scrollTop).toBe(0)
  expect(main.scrollLeft).toBe(0)
})

test('POP retries over animation frames until async content can accommodate the restore', () => {
  // Controllable rAF queue — stands in for content mounting under Suspense.
  let rafQueue: FrameRequestCallback[] = []
  vi.stubGlobal('requestAnimationFrame', (cb: FrameRequestCallback) => {
    rafQueue.push(cb)
    return rafQueue.length
  })
  vi.stubGlobal('cancelAnimationFrame', () => {})
  const flushRaf = () => {
    const queue = rafQueue
    rafQueue = []
    act(() => queue.forEach(cb => cb(performance.now())))
  }

  const main = setupMain()
  renderAt('/a')
  userScroll(main, 500)
  act(() => navigateFn('/b'))

  // Back to /a, but the page chunk hasn't rendered yet — container too short.
  Object.defineProperty(main, 'scrollHeight', { value: 600, configurable: true, writable: true })
  act(() => navigateFn(-1))
  expect(main.scrollTop).toBe(0) // can't fit yet — restore deferred
  expect(rafQueue.length).toBeGreaterThan(0)

  flushRaf() // still short — keeps waiting
  expect(main.scrollTop).toBe(0)

  // Content mounts; next frame restores.
  Object.defineProperty(main, 'scrollHeight', { value: 2000, configurable: true, writable: true })
  flushRaf()
  expect(main.scrollTop).toBe(500)
  expect(main.scrollLeft).toBe(0)
})
