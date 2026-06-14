import { describe, expect, it, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

vi.mock('../api/matching', () => ({ getMatches: vi.fn() }))
import { getMatches } from '../api/matching'
import TopMatchesPeek from '../pages/student/myspace/home/TopMatchesPeek'

const matches = vi.mocked(getMatches)

function renderPeek() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(<QueryClientProvider client={qc}><MemoryRouter><TopMatchesPeek /></MemoryRouter></QueryClientProvider>)
}

describe('TopMatchesPeek', () => {
  it('renders the top 3 matches with fitness % and hides extras', async () => {
    matches.mockResolvedValue([
      { program_id: 'p1', program_name: 'MS CS', institution_name: 'MIT', fitness_score: '0.82', band_label: 'reach' },
      { program_id: 'p2', program_name: 'MS DS', institution_name: 'CMU', fitness_score: '0.71', band_label: 'target' },
      { program_id: 'p3', program_name: 'MS AI', institution_name: 'Stanford', fitness_score: '0.6', band_label: 'safer' },
      { program_id: 'p4', program_name: 'Extra', institution_name: 'X', fitness_score: '0.5', band_label: 'safer' },
    ] as any)
    renderPeek()
    expect(await screen.findByText('MS CS')).toBeTruthy()
    expect(screen.getByText('82% fit')).toBeTruthy()
    expect(screen.queryByText('Extra')).toBeNull()
  })

  it('renders nothing when there are no matches', async () => {
    matches.mockResolvedValue([])
    const { container } = renderPeek()
    await waitFor(() => expect(container.querySelector('button')).toBeNull())
    expect(screen.queryByText('Your top matches')).toBeNull()
  })
})
