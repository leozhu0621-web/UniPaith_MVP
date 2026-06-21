import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import Table from '../components/ui/Table'

const columns = [
  { key: 'name', label: 'Name' },
  { key: 'score', label: 'Score', numeric: true, sortable: true },
]

const rows = [
  { id: '1', name: 'Ada', score: 92 },
  { id: '2', name: 'Ben', score: 81 },
  { id: '3', name: 'Cy', score: 74 },
]

describe('Table', () => {
  it('uses the shared empty-state semantics for empty data', () => {
    render(<Table columns={columns} data={[]} emptyMessage="No applicants found" />)

    expect(screen.getByRole('status')).toHaveTextContent('No applicants found')
  })

  it('announces loading skeletons as a busy table region', () => {
    render(<Table columns={columns} data={[]} isLoading />)

    expect(screen.getByRole('status', { name: 'Loading table' })).toHaveAttribute('aria-busy', 'true')
  })

  it('activates clickable rows with the keyboard', () => {
    const onRowClick = vi.fn()
    render(<Table columns={columns} data={rows} onRowClick={onRowClick} />)

    const row = screen.getByText('Ada').closest('tr')
    expect(row).toHaveAttribute('tabindex', '0')

    fireEvent.keyDown(row!, { key: 'Enter' })
    expect(onRowClick).toHaveBeenCalledWith(rows[0])

    fireEvent.keyDown(row!, { key: ' ' })
    expect(onRowClick).toHaveBeenCalledTimes(2)
  })

  it('labels pagination controls by action', () => {
    render(<Table columns={columns} data={rows} pageSize={2} />)

    expect(screen.getByText(/1.2 of 3/)).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Next page' }))

    expect(screen.getByText(/3.3 of 3/)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Previous page' })).not.toBeDisabled()
  })
})
