import { test, expect } from 'vitest'
import { render } from '@testing-library/react'
import StatBar from '../components/ui/StatBar'

// Under reduced motion StatBar mounts pre-drawn, so the fill width equals the
// computed magnitude immediately — assert that contract (no rAF flush needed).
function withReducedMotion(fn: () => void) {
  document.documentElement.setAttribute('data-reduce-motion', '')
  try {
    fn()
  } finally {
    document.documentElement.removeAttribute('data-reduce-motion')
  }
}

// The track is the outermost element; the fill is its only child.
function fillOf(container: HTMLElement): HTMLElement {
  return container.firstElementChild!.firstElementChild as HTMLElement
}

test('StatBar fills proportionally to value / max', () => {
  withReducedMotion(() => {
    const { container } = render(<StatBar value={30} max={120} />)
    expect(fillOf(container).style.width).toBe('25%')
  })
})

test('StatBar clamps an over-max value to a full bar', () => {
  withReducedMotion(() => {
    const { container } = render(<StatBar value={200} max={100} />)
    expect(fillOf(container).style.width).toBe('100%')
  })
})

test('StatBar renders an empty fill when max is zero', () => {
  withReducedMotion(() => {
    const { container } = render(<StatBar value={5} max={0} />)
    expect(fillOf(container).style.width).toBe('0%')
  })
})

test('StatBar tints the fill cobalt only when best', () => {
  withReducedMotion(() => {
    const plain = render(<StatBar value={1} max={2} />)
    expect(fillOf(plain.container).className).not.toContain('bg-secondary')

    const best = render(<StatBar value={1} max={2} best />)
    expect(fillOf(best.container).className).toContain('bg-secondary')
  })
})
