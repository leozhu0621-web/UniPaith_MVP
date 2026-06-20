import { test, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import Pagination from '../components/ui/Pagination'

test('renders nothing for a single page', () => {
  const { container } = render(<Pagination page={1} pageCount={1} onChange={() => {}} />)
  expect(container.querySelector('nav')).toBeNull()
})

test('renders every page when few, marks the current one', () => {
  render(<Pagination page={2} pageCount={4} onChange={() => {}} />)
  for (const n of ['1', '2', '3', '4']) expect(screen.getByRole('button', { name: `Page ${n}` })).toBeTruthy()
  expect(screen.getByRole('button', { name: 'Page 2' })).toHaveAttribute('aria-current', 'page')
})

test('collapses long ranges with ellipsis', () => {
  render(<Pagination page={10} pageCount={20} onChange={() => {}} />)
  // first, last, and the window around current are present; a mid page is not.
  expect(screen.getByRole('button', { name: 'Page 1' })).toBeTruthy()
  expect(screen.getByRole('button', { name: 'Page 20' })).toBeTruthy()
  expect(screen.getByRole('button', { name: 'Page 10' })).toBeTruthy()
  expect(screen.queryByRole('button', { name: 'Page 5' })).toBeNull()
})

test('disables prev on the first page and next on the last', () => {
  const { rerender } = render(<Pagination page={1} pageCount={5} onChange={() => {}} />)
  expect(screen.getByRole('button', { name: 'Previous page' })).toBeDisabled()
  expect(screen.getByRole('button', { name: 'Next page' })).not.toBeDisabled()
  rerender(<Pagination page={5} pageCount={5} onChange={() => {}} />)
  expect(screen.getByRole('button', { name: 'Next page' })).toBeDisabled()
})

test('fires onChange with the chosen page', () => {
  const onChange = vi.fn()
  render(<Pagination page={2} pageCount={5} onChange={onChange} />)
  fireEvent.click(screen.getByRole('button', { name: 'Page 4' }))
  expect(onChange).toHaveBeenCalledWith(4)
  fireEvent.click(screen.getByRole('button', { name: 'Next page' }))
  expect(onChange).toHaveBeenCalledWith(3)
})
