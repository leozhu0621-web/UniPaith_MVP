import { useEffect } from 'react'

const APP_SUFFIX = ' · UniPaith'

/** Sets document.title for the current route (Spec/04 §15). */
export default function usePageTitle(title: string) {
  useEffect(() => {
    const prev = document.title
    document.title = title.endsWith('UniPaith') ? title : `${title}${APP_SUFFIX}`
    return () => { document.title = prev }
  }, [title])
}
