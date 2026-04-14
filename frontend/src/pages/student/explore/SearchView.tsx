import { lazy, Suspense } from 'react'

// The old DiscoverPage has the full search/filter/NLP engine — reuse it as the search view
const OldDiscoverSearch = lazy(() => import('../DiscoverPage').then(m => ({ default: m.DiscoverSearchView ?? m.default })))

export default function SearchView() {
  return (
    <Suspense fallback={<div className="py-10 text-center text-student-text">Loading search...</div>}>
      <OldDiscoverSearch />
    </Suspense>
  )
}
