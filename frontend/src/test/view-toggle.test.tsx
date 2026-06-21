import { test, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, renderHook, act } from '@testing-library/react'
import ViewToggle from '../components/ui/ViewToggle'
import useBrowseView from '../hooks/useBrowseView'

const KEY = 'unipaith:browseView'
beforeEach(() => localStorage.removeItem(KEY))

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

// useBrowseView — the shared grid/list preference behind the toggle.
test('useBrowseView defaults to grid when nothing is stored', () => {
  const { result } = renderHook(() => useBrowseView())
  expect(result.current[0]).toBe('grid')
})

test('useBrowseView reads a stored list preference on init', () => {
  localStorage.setItem(KEY, 'list')
  const { result } = renderHook(() => useBrowseView())
  expect(result.current[0]).toBe('list')
})

test('useBrowseView persists the chosen view', () => {
  const { result } = renderHook(() => useBrowseView())
  act(() => result.current[1]('list'))
  expect(result.current[0]).toBe('list')
  expect(localStorage.getItem(KEY)).toBe('list')
})
