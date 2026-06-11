/**
 * My Space › Prep › Recommenders (Spec 2026-06-10 §5) — request and track
 * recommendation letters, moved from Profile › Preparation.
 */
import { lazy, Suspense } from 'react'

const RecommendationsPage = lazy(() => import('../../RecommendationsPage'))

export default function RecommendersTab() {
  return (
    <div className="w-full px-4 sm:px-6 py-6">
      <Suspense fallback={<p className="text-sm text-muted-foreground">Loading recommenders…</p>}>
        <RecommendationsPage />
      </Suspense>
    </div>
  )
}
