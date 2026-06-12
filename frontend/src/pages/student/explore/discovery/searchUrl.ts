import { encodeChipsParam } from './chipUtils'
import { encodeFiltersParam } from './filterUtils'
import type { SavedSearch } from '../../../../api/savedSearches'

/** Rebuild the /s/explore URL that restores a saved search's exact state. */
export function exploreUrlFromSavedQuery(query: SavedSearch['query'] | undefined | null): string {
  const p = new URLSearchParams()
  const q = query?.query
  if (q && q.trim()) p.set('q', q.trim())
  if (query?.chips && query.chips.length) p.set('chips', encodeChipsParam(query.chips))
  if (query?.filters && Object.keys(query.filters).length)
    p.set('filters', encodeFiltersParam(query.filters))
  if (query?.sort && query.sort !== 'relevance') p.set('sort', query.sort)
  const qs = p.toString()
  return qs ? `/s/explore?${qs}` : '/s/explore'
}
