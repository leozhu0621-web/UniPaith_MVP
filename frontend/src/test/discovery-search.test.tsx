import { describe, expect, it, vi } from 'vitest'
import { fireEvent, render, screen } from '@testing-library/react'

import ConstraintChips from '../pages/student/explore/discovery/ConstraintChips'
import GenreTiles from '../pages/student/explore/discovery/GenreTiles'
import {
  decodeRange,
  encodeChipsParam,
  encodeRange,
  formatBudgetDisplay,
  formatDurationDisplay,
  parseChipsParam,
} from '../pages/student/explore/discovery/chipUtils'
import type { ConstraintChip } from '../types/search'

// Spec 10 — Discovery type-first search (chip utils + chip strip + genre tiles).

describe('chipUtils — URL chip state', () => {
  it('round-trips chips through the URL param (Spec §10)', () => {
    const chips: ConstraintChip[] = [
      { id: 'major:computer science', category: 'major', value: 'computer science', display: 'Computer Science', confidence: 90, user_confirmed: true },
      { id: 'budget:<=50000', category: 'budget', value: '<=50000', display: '≤ $50k/yr', confidence: 88 },
    ]
    const parsed = parseChipsParam(encodeChipsParam(chips))
    expect(parsed).toHaveLength(2)
    expect(parsed[0]).toMatchObject({ category: 'major', value: 'computer science' })
    expect(parsed[1]).toMatchObject({ category: 'budget', value: '<=50000' })
  })

  it('drops malformed / unknown chips rather than throwing', () => {
    expect(parseChipsParam('not-json')).toEqual([])
    expect(parseChipsParam(null)).toEqual([])
    const mixed = JSON.stringify([
      { category: 'bogus', value: 'x' },
      { category: 'major', value: '' },
      { category: 'location', value: 'California', display: 'California', confidence: 85 },
    ])
    const parsed = parseChipsParam(mixed)
    expect(parsed).toHaveLength(1)
    expect(parsed[0].category).toBe('location')
  })

  it('encodes/decodes numeric ranges', () => {
    expect(decodeRange('<=50000')).toEqual({ max: 50000 })
    expect(decodeRange('>=20000')).toEqual({ min: 20000 })
    expect(decodeRange('20000-50000')).toEqual({ min: 20000, max: 50000 })
    expect(encodeRange({ min: 20000, max: 50000 })).toBe('20000-50000')
    expect(encodeRange({ max: 50000 })).toBe('<=50000')
    expect(encodeRange({})).toBe('')
  })

  it('formats budget + duration display labels', () => {
    expect(formatBudgetDisplay({ max: 50000 })).toBe('≤ $50k/yr')
    expect(formatBudgetDisplay({ min: 20000, max: 50000 })).toBe('$20k–$50k/yr')
    expect(formatDurationDisplay({ max: 24 })).toBe('≤ 2 yr')
    expect(formatDurationDisplay({ min: 18, max: 18 })).toBe('≤ 18 mo')
  })
})

describe('ConstraintChips', () => {
  const chip: ConstraintChip = {
    id: 'degree_level:masters',
    category: 'degree_level',
    value: 'masters',
    display: "Master's",
    confidence: 95,
    user_confirmed: false,
  }

  it('renders a chip as Category · Value', () => {
    render(
      <ConstraintChips chips={[chip]} onApplyEdit={vi.fn()} onRemove={vi.fn()} onAdd={vi.fn()} onConfirm={vi.fn()} />,
    )
    expect(screen.getByText('Degree')).toBeInTheDocument()
    expect(screen.getByText("Master's")).toBeInTheDocument()
    expect(screen.getByText('Add')).toBeInTheDocument()
  })

  it('removes a chip via the ✕ button', () => {
    const onRemove = vi.fn()
    render(
      <ConstraintChips chips={[chip]} onApplyEdit={vi.fn()} onRemove={onRemove} onAdd={vi.fn()} onConfirm={vi.fn()} />,
    )
    fireEvent.click(screen.getByLabelText("Remove Degree Master's"))
    expect(onRemove).toHaveBeenCalledWith('degree_level:masters')
  })
})

describe('GenreTiles', () => {
  it('renders tiles and reports the picked genre as a major chip seed', () => {
    const onPick = vi.fn()
    render(<GenreTiles onPick={onPick} />)
    expect(screen.getByText('Computer Science')).toBeInTheDocument()
    fireEvent.click(screen.getByText('Business'))
    expect(onPick).toHaveBeenCalledWith({ value: 'business', label: 'Business' })
  })
})
