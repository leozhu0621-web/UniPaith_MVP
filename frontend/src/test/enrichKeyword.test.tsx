/**
 * Tests for the keyword and typeahead enrichment widgets.
 * Tests the KeywordPicker and TypeaheadPicker sub-components exported from EnrichWidget.
 */
import { test, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'

import { KeywordPicker, TypeaheadPicker } from '../components/student/EnrichWidget'

// ── KeywordPicker ──────────────────────────────────────────────────────────

test('keyword: selecting a suggestion chip and adding a custom chip submits a string[]', () => {
  const onSubmit = vi.fn()
  render(
    <KeywordPicker
      options={['Research', 'Diversity', 'Innovation']}
      onSubmit={onSubmit}
    />
  )

  // Pick a suggestion chip
  fireEvent.click(screen.getByRole('button', { name: 'Research' }))

  // Add a custom chip via the add-your-own input
  const input = screen.getByPlaceholderText(/add your own/i)
  fireEvent.change(input, { target: { value: 'Community' } })
  fireEvent.keyDown(input, { key: 'Enter' })

  // Submit
  fireEvent.click(screen.getByRole('button', { name: /save|continue/i }))

  expect(onSubmit).toHaveBeenCalledWith(['Research', 'Community'])
})

test('keyword: selecting only suggestion chips submits the string[]', () => {
  const onSubmit = vi.fn()
  render(
    <KeywordPicker
      options={['Research', 'Diversity', 'Innovation']}
      onSubmit={onSubmit}
    />
  )

  fireEvent.click(screen.getByRole('button', { name: 'Diversity' }))
  fireEvent.click(screen.getByRole('button', { name: 'Innovation' }))
  fireEvent.click(screen.getByRole('button', { name: /save|continue/i }))

  expect(onSubmit).toHaveBeenCalledWith(['Diversity', 'Innovation'])
})

test('keyword: submit button is disabled when nothing is selected', () => {
  const onSubmit = vi.fn()
  render(
    <KeywordPicker
      options={['Research', 'Diversity']}
      onSubmit={onSubmit}
    />
  )

  const submitBtn = screen.getByRole('button', { name: /save|continue/i })
  expect(submitBtn).toBeDisabled()
})

test('keyword: deselecting a chip removes it from the selection', () => {
  const onSubmit = vi.fn()
  render(
    <KeywordPicker
      options={['Research', 'Diversity']}
      onSubmit={onSubmit}
    />
  )

  fireEvent.click(screen.getByRole('button', { name: 'Research' }))
  fireEvent.click(screen.getByRole('button', { name: 'Diversity' }))
  // Deselect Research
  fireEvent.click(screen.getByRole('button', { name: 'Research' }))
  fireEvent.click(screen.getByRole('button', { name: /save|continue/i }))

  expect(onSubmit).toHaveBeenCalledWith(['Diversity'])
})

// ── TypeaheadPicker ────────────────────────────────────────────────────────

test('typeahead: clicking a common-country chip submits that string', () => {
  const onSubmit = vi.fn()
  render(<TypeaheadPicker onSubmit={onSubmit} />)

  // There should be some common-country chips visible
  const usChip = screen.getByRole('button', { name: 'United States' })
  fireEvent.click(usChip)

  expect(onSubmit).toHaveBeenCalledWith('United States')
})

test('typeahead: typing a search query filters results and clicking one submits it', () => {
  const onSubmit = vi.fn()
  render(<TypeaheadPicker onSubmit={onSubmit} />)

  const searchInput = screen.getByPlaceholderText(/search/i)
  fireEvent.change(searchInput, { target: { value: 'Ger' } })

  // Germany should appear in results
  const germanyBtn = screen.getByRole('button', { name: 'Germany' })
  fireEvent.click(germanyBtn)

  expect(onSubmit).toHaveBeenCalledWith('Germany')
})

test('typeahead: search results exclude already shown common countries to avoid duplicates when query matches', () => {
  const onSubmit = vi.fn()
  render(<TypeaheadPicker onSubmit={onSubmit} />)

  // When we type "United States" it should show in one of the two places but not both
  const searchInput = screen.getByPlaceholderText(/search/i)
  fireEvent.change(searchInput, { target: { value: 'United States' } })

  // Should still be accessible
  const btns = screen.getAllByRole('button', { name: 'United States' })
  // There should be exactly one button with this label (either chip or search result, not both)
  expect(btns.length).toBe(1)
  fireEvent.click(btns[0])
  expect(onSubmit).toHaveBeenCalledWith('United States')
})
