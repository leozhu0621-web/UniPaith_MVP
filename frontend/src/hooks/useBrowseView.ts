import { useEffect, useState } from 'react'

export type BrowseView = 'grid' | 'list'

const KEY = 'unipaith:browseView'

/**
 * One shared grid/list preference across every browse surface (universities,
 * program search), so the toggle behaves consistently and the choice is
 * remembered everywhere. Defaults to grid.
 */
export default function useBrowseView(): [BrowseView, (v: BrowseView) => void] {
  const [view, setView] = useState<BrowseView>(() => {
    const v = typeof localStorage !== 'undefined' ? localStorage.getItem(KEY) : null
    return v === 'list' ? 'list' : 'grid'
  })
  useEffect(() => {
    try { localStorage.setItem(KEY, view) } catch { /* ignore */ }
  }, [view])
  return [view, setView]
}
