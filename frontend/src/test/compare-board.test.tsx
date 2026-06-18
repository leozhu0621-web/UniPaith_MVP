// Feature #3 — saved compare board sort logic + render.
import { describe, it, expect } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { sortRows } from '../pages/student/saved/compareSort'
import CompareBoard from '../pages/student/saved/CompareBoard'
import type { SavedProgram } from '../types'

const sp = (over: Partial<SavedProgram>): SavedProgram =>
  ({ program_id: Math.random().toString(36), program_name: 'P', ...over } as SavedProgram)

describe('sortRows', () => {
  it('sorts tuition ascending with nulls last', () => {
    const rows = sortRows(
      [sp({ tuition: 40000 }), sp({ tuition: null }), sp({ tuition: 20000 })],
      'tuition',
      'asc',
    )
    expect(rows.map(r => r.tuition)).toEqual([20000, 40000, null])
  })

  it('descending keeps nulls last (not flipped to front)', () => {
    const rows = sortRows([sp({ tuition: 40000 }), sp({ tuition: null }), sp({ tuition: 20000 })], 'tuition', 'desc')
    expect(rows.map(r => r.tuition)).toEqual([40000, 20000, null])
  })

  it('band asc is reach → target → safer', () => {
    const rows = sortRows([sp({ band_label: 'safer' }), sp({ band_label: 'reach' }), sp({ band_label: 'target' })], 'band', 'asc')
    expect(rows.map(r => r.band_label)).toEqual(['reach', 'target', 'safer'])
  })
})

describe('CompareBoard', () => {
  it('renders a row per saved program and flags a reach-heavy list', () => {
    render(
      <MemoryRouter>
        <CompareBoard
          programs={[
            sp({ program_name: 'Alpha', band_label: 'reach' }),
            sp({ program_name: 'Beta', band_label: 'reach' }),
            sp({ program_name: 'Gamma', band_label: 'safer' }),
          ]}
        />
      </MemoryRouter>,
    )
    expect(screen.getByText('Alpha')).toBeTruthy()
    expect(screen.getByText('Gamma')).toBeTruthy()
    expect(screen.getByText(/reach-heavy/i)).toBeTruthy()
    // header is interactive (sortable)
    fireEvent.click(screen.getByRole('button', { name: /sort by tuition/i }))
  })
})
