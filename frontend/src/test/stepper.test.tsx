import { test, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import Stepper from '../components/ui/Stepper'

const STEPS = [
  { key: 'accepted', label: 'Accepted' },
  { key: 'intent_confirmed', label: 'Confirmed' },
  { key: 'deposit_recorded', label: 'Deposit' },
  { key: 'enrollment_confirmed', label: 'Verified' },
  { key: 'enrolled', label: 'Enrolled' },
]

test('Stepper renders every step label', () => {
  render(<Stepper steps={STEPS} currentKey="deposit_recorded" />)
  for (const s of STEPS) {
    expect(screen.getByText(s.label)).toBeInTheDocument()
  }
})

test('Stepper marks the current step with aria-current', () => {
  const { container } = render(<Stepper steps={STEPS} currentKey="deposit_recorded" />)
  const current = container.querySelectorAll('[aria-current="step"]')
  expect(current).toHaveLength(1)
  expect(current[0]).toHaveTextContent('Deposit')
})

test('Stepper uses ordered-list semantics', () => {
  const { container } = render(<Stepper steps={STEPS} currentKey="accepted" />)
  expect(container.querySelector('ol')).not.toBeNull()
  expect(container.querySelectorAll('li')).toHaveLength(STEPS.length)
})

test('Stepper shows a check on done steps (before the current one)', () => {
  // currentKey at index 2 → 2 done steps render a check (lucide svg), not a number.
  const { container } = render(<Stepper steps={STEPS} currentKey="deposit_recorded" />)
  const checks = container.querySelectorAll('li svg')
  expect(checks).toHaveLength(2)
})

test('Stepper tolerates an unknown currentKey (falls back to the first step)', () => {
  const { container } = render(<Stepper steps={STEPS} currentKey="nope" />)
  const current = container.querySelectorAll('[aria-current="step"]')
  expect(current).toHaveLength(1)
  expect(current[0]).toHaveTextContent('Accepted')
})
