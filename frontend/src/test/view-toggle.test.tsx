import { test, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import ViewToggle from '../components/ui/ViewToggle'

test('renders grid + list buttons and marks the active one', () => {
  render(<ViewToggle value="grid" onChange={() => {}} />)
  const grid = screen.getByRole('button', { name: 'Grid view' })
  const list = screen.getByRole('button', { name: 'List view' })
  expect(grid).toHaveAttribute('aria-pressed', 'true')
  expect(list).toHaveAttribute('aria-pressed', 'false')
})

test('fires onChange with the chosen view', () => {
  const onChange = vi.fn()
  render(<ViewToggle value="grid" onChange={onChange} />)
  fireEvent.click(screen.getByRole('button', { name: 'List view' }))
  expect(onChange).toHaveBeenCalledWith('list')
})

test('reflects the list value', () => {
  render(<ViewToggle value="list" onChange={() => {}} />)
  expect(screen.getByRole('button', { name: 'List view' })).toHaveAttribute('aria-pressed', 'true')
})
