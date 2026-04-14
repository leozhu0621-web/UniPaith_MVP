import { lazy, Suspense } from 'react'

const SavedListPage = lazy(() => import('../SavedListPage'))

export default function SavedView() {
  return (
    <Suspense fallback={<div className="py-10 text-center text-student-text">Loading saved programs...</div>}>
      <SavedListPage />
    </Suspense>
  )
}
