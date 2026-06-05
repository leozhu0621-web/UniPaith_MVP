import { useEffect } from 'react'
import { useLocation } from 'react-router-dom'

// Reset the main scroll container to the top on every route change. The
// `<main id="main">` scroll container persists across navigations (only its
// keyed child remounts), so without this a tall page can open mid-scroll if you
// navigated from a scrolled one. Skips when there's a hash so in-page anchor
// links still scroll to their target. Mount once near the layout root.
export default function ScrollReset() {
  const { pathname, hash } = useLocation()
  useEffect(() => {
    if (hash) return
    const main = document.getElementById('main')
    if (main) main.scrollTop = 0
    else window.scrollTo(0, 0)
  }, [pathname, hash])
  return null
}
