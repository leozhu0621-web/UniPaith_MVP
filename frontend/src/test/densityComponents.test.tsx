import { test, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { PageHeader, SectionHeader, ListRow, StatTile } from '../components/student/density'

test('SectionHeader renders label + count', () => {
  render(<SectionHeader count={5}>Recently viewed</SectionHeader>)
  expect(screen.getByText('Recently viewed')).toBeInTheDocument()
  expect(screen.getByText('5')).toBeInTheDocument()
})

test('PageHeader renders eyebrow, title, count, sub', () => {
  render(<PageHeader eyebrow="Match" title="Your matches" count={12} sub="Ranked for fit" />)
  expect(screen.getByText('Match')).toBeInTheDocument()
  expect(screen.getByRole('heading', { name: /Your matches/ })).toBeInTheDocument()
  expect(screen.getByText('12')).toBeInTheDocument()
  expect(screen.getByText('Ranked for fit')).toBeInTheDocument()
})

test('ListRow renders title + sub + trailing and fires onClick', () => {
  const onClick = vi.fn()
  render(<ListRow title="Computer Science" sub="MIT · MS" trailing={<span>›</span>} onClick={onClick} />)
  expect(screen.getByText('Computer Science')).toBeInTheDocument()
  expect(screen.getByText('MIT · MS')).toBeInTheDocument()
  fireEvent.click(screen.getByRole('button'))
  expect(onClick).toHaveBeenCalledTimes(1)
})

test('ListRow without onClick renders a non-interactive row', () => {
  render(<ListRow title="Static row" />)
  expect(screen.getByText('Static row')).toBeInTheDocument()
  expect(screen.queryByRole('button')).not.toBeInTheDocument()
})

test('StatTile renders value + label + sub', () => {
  render(<StatTile value={3} label="In progress" sub="2 due soon" />)
  expect(screen.getByText('3')).toBeInTheDocument()
  expect(screen.getByText('In progress')).toBeInTheDocument()
  expect(screen.getByText('2 due soon')).toBeInTheDocument()
})
