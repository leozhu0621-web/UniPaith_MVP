export const CELEBRATE_KEY = 'myspace_celebrated'

function read(): Set<string> {
  try {
    const raw = localStorage.getItem(CELEBRATE_KEY)
    if (!raw) return new Set()
    const arr = JSON.parse(raw)
    return Array.isArray(arr) ? new Set(arr.map(String)) : new Set()
  } catch {
    return new Set()
  }
}

/** Win ids not yet celebrated. */
export function freshWinIds(ids: string[]): string[] {
  const seen = read()
  return ids.filter(id => !seen.has(id))
}

/** Persist that these win ids have had their one gold beat. */
export function markCelebrated(ids: string[]): void {
  if (!ids.length) return
  try {
    const seen = read()
    ids.forEach(id => seen.add(id))
    localStorage.setItem(CELEBRATE_KEY, JSON.stringify([...seen]))
  } catch {
    /* ignore — celebration is best-effort */
  }
}
