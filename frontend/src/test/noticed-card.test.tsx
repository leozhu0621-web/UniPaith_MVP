import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

import NoticedCard, { noticedItemsFromSignals } from '../pages/student/discover/NoticedCard'
import * as livingProfile from '../api/livingProfile'

function renderCard(ui: React.ReactNode) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(<QueryClientProvider client={qc}>{ui}</QueryClientProvider>)
}

describe('noticedItemsFromSignals', () => {
  it('pulls readable labels from goals/needs/identity blocks', () => {
    const items = noticedItemsFromSignals({
      goals: [{ specific: 'study marine biology' }],
      needs: [{ signal: 'strong financial aid' }],
      identity: [{ value: 'curiosity' }],
      basic: { gpa: 3.9 },
    })
    expect(items.map(i => i.label)).toEqual([
      'study marine biology',
      'strong financial aid',
      'curiosity',
    ])
  })

  it('returns nothing for null signals', () => {
    expect(noticedItemsFromSignals(null)).toEqual([])
  })
})

describe('NoticedCard', () => {
  beforeEach(() => vi.restoreAllMocks())

  it('reflects a noticed signal and edits it inline via updateSignal', async () => {
    const spy = vi
      .spyOn(livingProfile, 'updateSignal')
      .mockResolvedValue({ id: 'g1' } as never)
    renderCard(
      <NoticedCard items={[{ label: 'study marine biology', ref: { kind: 'goal', id: 'g1' } }]} />,
    )
    expect(screen.getByTestId('noticed-card')).toBeInTheDocument()
    expect(screen.getByText('Noticed')).toBeInTheDocument()

    fireEvent.click(screen.getByLabelText('Tweak: study marine biology'))
    const input = screen.getByLabelText('Edit what Uni noticed') as HTMLInputElement
    fireEvent.change(input, { target: { value: 'study marine ecology' } })
    fireEvent.keyDown(input, { key: 'Enter' })

    await waitFor(() =>
      expect(spy).toHaveBeenCalledWith({ kind: 'goal', id: 'g1', value: 'study marine ecology' }),
    )
  })

  it('renders nothing when there are no items', () => {
    const { container } = renderCard(<NoticedCard items={[]} />)
    expect(container.querySelector('[data-testid="noticed-card"]')).toBeNull()
  })
})
