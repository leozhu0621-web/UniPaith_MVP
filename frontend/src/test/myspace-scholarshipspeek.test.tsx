import { describe, expect, it, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

vi.mock('../api/students', () => ({ getScholarshipMatches: vi.fn() }))
import { getScholarshipMatches } from '../api/students'
import ScholarshipsPeek from '../pages/student/myspace/home/ScholarshipsPeek'

const sch = vi.mocked(getScholarshipMatches)

function renderPeek() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(<QueryClientProvider client={qc}><MemoryRouter><ScholarshipsPeek /></MemoryRouter></QueryClientProvider>)
}

describe('ScholarshipsPeek', () => {
  it('renders matched scholarships with formatted amount + type', async () => {
    sch.mockResolvedValue([
      { scholarship_id: 's1', name: 'Merit Grant', award_estimate: 10000, reasons: ['Strong GPA'], scholarship_type: 'merit_based' },
    ] as any)
    renderPeek()
    expect(await screen.findByText('Merit Grant')).toBeTruthy()
    expect(screen.getByText('Merit Based')).toBeTruthy()
    expect(screen.getByText(/\$10,000/)).toBeTruthy()
  })

  it('renders nothing when there are no scholarship matches', async () => {
    sch.mockResolvedValue([])
    const { container } = renderPeek()
    await waitFor(() => expect(container.querySelector('button')).toBeNull())
    expect(screen.queryByText('Scholarships you may qualify for')).toBeNull()
  })
})
