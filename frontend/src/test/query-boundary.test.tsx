import { fireEvent, render, screen } from '@testing-library/react'
import type { UseQueryResult } from '@tanstack/react-query'
import { describe, expect, it, vi } from 'vitest'

import QueryBoundary from '../components/ui/QueryBoundary'
import { COPY } from '../lib/copy'

type BoundaryQuery<TData> = Pick<UseQueryResult<TData, unknown>, 'data' | 'isError' | 'isLoading' | 'refetch'>

function query<TData>(overrides: Partial<BoundaryQuery<TData>>): BoundaryQuery<TData> {
  return {
    data: undefined,
    isError: false,
    isLoading: false,
    refetch: vi.fn(),
    ...overrides,
  } as unknown as BoundaryQuery<TData>
}

describe('QueryBoundary', () => {
  it('does not expose raw thrown error messages by default', () => {
    const refetch = vi.fn()
    const failingQuery = {
      ...query<string[]>({
        isError: true,
        refetch,
      }),
      error: new Error('ECONNREFUSED database stack trace'),
    } as unknown as BoundaryQuery<string[]>

    render(
      <QueryBoundary
        query={failingQuery}
        loadingFallback={<p>Loading</p>}
      >
        {() => <p>Loaded</p>}
      </QueryBoundary>
    )

    expect(screen.getByRole('alert')).toHaveTextContent(COPY.errLoad)
    expect(screen.getByRole('alert')).toHaveTextContent(COPY.errRetry)
    expect(screen.queryByText(/stack trace|ECONNREFUSED|TypeError/i)).toBeNull()

    fireEvent.click(screen.getByRole('button', { name: COPY.errRetryAction }))
    expect(refetch).toHaveBeenCalledTimes(1)
  })

  it('uses caller-provided product copy for known error states', () => {
    render(
      <QueryBoundary
        query={query<string[]>({ isError: true })}
        loadingFallback={<p>Loading</p>}
        errorTitle="Templates couldn't load."
        errorDetail="You can still start a regular chat."
      >
        {() => <p>Loaded</p>}
      </QueryBoundary>
    )

    expect(screen.getByRole('alert')).toHaveTextContent("Templates couldn't load.")
    expect(screen.getByRole('alert')).toHaveTextContent('You can still start a regular chat.')
  })

  it('renders loading, empty, and data branches', () => {
    const { rerender } = render(
      <QueryBoundary query={query<string[]>({ isLoading: true })} loadingFallback={<p>Loading templates</p>}>
        {() => <p>Loaded</p>}
      </QueryBoundary>
    )
    expect(screen.getByText('Loading templates')).toBeInTheDocument()

    rerender(
      <QueryBoundary
        query={query<string[]>({ data: [] })}
        loadingFallback={<p>Loading templates</p>}
        isEmpty={(items) => items.length === 0}
        emptyFallback={<p>No templates available.</p>}
      >
        {(items) => <p>{items.length} templates</p>}
      </QueryBoundary>
    )
    expect(screen.getByText('No templates available.')).toBeInTheDocument()

    rerender(
      <QueryBoundary query={query<string[]>({ data: ['one'] })} loadingFallback={<p>Loading templates</p>}>
        {(items) => <p>{items.length} template</p>}
      </QueryBoundary>
    )
    expect(screen.getByText('1 template')).toBeInTheDocument()
  })
})
