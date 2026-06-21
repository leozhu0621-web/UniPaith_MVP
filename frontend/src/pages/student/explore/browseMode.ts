// Academic › Universities holds two distinct searches over two entity types.
// The mode is an EXPLICIT choice (Discover review 2026-06-19 #3), owned by the
// ?umode= URL param. When unset it follows the URL so a shared program-search
// deep-link (chips/filters present → searchActive) still opens in Programs;
// otherwise it defaults to Universities, matching the sub-tab's name.
export type BrowseMode = 'programs' | 'universities'

export function resolveBrowseMode(umode: string | null, searchActive: boolean): BrowseMode {
  if (umode === 'programs' || umode === 'universities') return umode
  return searchActive ? 'programs' : 'universities'
}
