import { isRouteErrorResponse, useNavigate, useRouteError } from 'react-router-dom'

export default function RouteErrorPage() {
  const error = useRouteError()
  const navigate = useNavigate()

  const message = isRouteErrorResponse(error)
    ? `${error.status} ${error.statusText}`
    : error instanceof Error
      ? error.message
      : 'An unexpected page error occurred.'

  return (
    <div className="min-h-screen bg-background px-4 py-16">
      <div className="mx-auto max-w-xl rounded-2xl border border-border bg-card p-6 shadow-sm">
        <h1 className="text-lg font-semibold text-foreground">Page unavailable right now</h1>
        <p className="mt-2 text-sm text-muted-foreground">
          We hit an unexpected issue loading this page. You can safely return to dashboard and continue.
        </p>
        <p className="mt-2 text-xs text-muted-foreground">{message}</p>
        <div className="mt-4 flex gap-2">
          <button
            type="button"
            onClick={() => navigate('/s/dashboard')}
            className="inline-flex rounded-lg bg-secondary px-4 py-2 text-sm font-medium text-secondary-foreground hover:bg-secondary/90"
          >
            Go to dashboard
          </button>
          <button
            type="button"
            onClick={() => window.location.reload()}
            className="inline-flex rounded-lg border border-border bg-card px-4 py-2 text-sm font-medium text-foreground hover:bg-muted"
          >
            Reload page
          </button>
        </div>
      </div>
    </div>
  )
}
