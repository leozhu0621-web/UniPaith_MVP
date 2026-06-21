import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import QueryError from '../components/ui/QueryError'
import { COPY } from '../lib/copy'

describe('QueryError', () => {
  it('uses the shared no-blame copy and retry action by default', () => {
    const onRetry = vi.fn()
    render(<QueryError onRetry={onRetry} />)

    expect(screen.getByRole('alert')).toHaveTextContent(COPY.errLoad)
    expect(screen.getByRole('alert')).toHaveTextContent(COPY.errRetry)

    fireEvent.click(screen.getByRole('button', { name: COPY.errRetryAction }))
    expect(onRetry).toHaveBeenCalledTimes(1)
  })

  it('keeps custom detail while preserving the shared retry label', () => {
    const onRetry = vi.fn()
    render(<QueryError detail="We couldn't load the priority queue." onRetry={onRetry} />)

    expect(screen.getByText("We couldn't load the priority queue.")).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: COPY.errRetryAction }))
    expect(onRetry).toHaveBeenCalledTimes(1)
  })
})
