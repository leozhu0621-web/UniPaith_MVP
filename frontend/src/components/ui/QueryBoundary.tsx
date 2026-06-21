import type { ReactNode } from 'react'
import type { UseQueryResult } from '@tanstack/react-query'
import QueryError from './QueryError'

interface QueryBoundaryProps<TData> {
  query: Pick<UseQueryResult<TData, unknown>, 'data' | 'error' | 'isError' | 'isLoading' | 'refetch'>
  children: (data: TData) => ReactNode
  loadingFallback: ReactNode
  emptyFallback?: ReactNode
  errorTitle?: string
  errorDetail?: string
  isEmpty?: (data: TData) => boolean
  variant?: 'block' | 'inline' | 'row'
}

function detailFromError(error: unknown, fallback?: string) {
  if (fallback) return fallback
  if (error instanceof Error && error.message) return error.message
  return undefined
}

export default function QueryBoundary<TData>({
  query,
  children,
  loadingFallback,
  emptyFallback,
  errorTitle,
  errorDetail,
  isEmpty,
  variant = 'block',
}: QueryBoundaryProps<TData>) {
  if (query.isLoading) return <>{loadingFallback}</>

  if (query.isError) {
    return (
      <QueryError
        title={errorTitle}
        detail={detailFromError(query.error, errorDetail)}
        variant={variant}
        onRetry={() => {
          void query.refetch()
        }}
      />
    )
  }

  if (query.data === undefined) return <>{emptyFallback ?? null}</>
  if (isEmpty?.(query.data)) return <>{emptyFallback ?? null}</>

  return <>{children(query.data)}</>
}
