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
    <div className="min-h-screen bg-slate-50 px-4 py-16">
      <div className="mx-auto max-w-xl rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <h1 className="text-lg font-semibold text-slate-900">Page unavailable right now</h1>
        <p className="mt-2 text-sm text-slate-600">
          We hit an unexpected issue loading this page. You can safely return to dashboard and continue.
        </p>
        <p className="mt-2 text-xs text-slate-500">{message}</p>
        <div className="mt-4 flex gap-2">
          <button
            type="button"
            onClick={() => navigate('/s/dashboard')}
            className="inline-flex rounded-lg bg-brand-slate-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-slate-700"
          >
            Go to dashboard
          </button>
          <button
            type="button"
            onClick={() => window.location.reload()}
            className="inline-flex rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
          >
            Reload page
          </button>
        </div>
      </div>
    </div>
  )
}
