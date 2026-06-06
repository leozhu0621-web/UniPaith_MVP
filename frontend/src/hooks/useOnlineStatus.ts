import { useEffect, useState } from 'react'

/**
 * Tracks browser online/offline status (Spec 78 §5).
 * Returns `true` when the browser reports a connection, `false` when offline.
 * Used by StudentLayout to surface an app-wide offline banner so a dropped
 * connection never silently degrades into blank-on-error surfaces.
 */
export function useOnlineStatus(): boolean {
  const [online, setOnline] = useState(() =>
    typeof navigator === 'undefined' ? true : navigator.onLine,
  )

  useEffect(() => {
    const goOnline = () => setOnline(true)
    const goOffline = () => setOnline(false)
    window.addEventListener('online', goOnline)
    window.addEventListener('offline', goOffline)
    return () => {
      window.removeEventListener('online', goOnline)
      window.removeEventListener('offline', goOffline)
    }
  }, [])

  return online
}
