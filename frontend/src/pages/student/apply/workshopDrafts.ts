/**
 * Workshop draft persistence (Ship D — input preservation).
 *
 * Essay/interview drafts are typed into plain textareas with no backend
 * "draft" concept — navigating away used to destroy them. Drafts now persist
 * to localStorage keyed per program (`<prefix>:<programId|general>`), with a
 * `<prefix>:last` pointer so a fresh mount restores whatever the student was
 * last working on, program selection included.
 *
 * All storage access is try/catch-guarded — private-mode/quota failures
 * degrade to the old (non-persisting) behavior, never a crash.
 */

const GENERAL = 'general'

function storageKey(prefix: string, programId: string | null | undefined): string {
  return `${prefix}:${programId || GENERAL}`
}

function safeGet(key: string): string | null {
  try {
    return window.localStorage.getItem(key)
  } catch {
    return null
  }
}

function safeSet(key: string, value: string): void {
  try {
    window.localStorage.setItem(key, value)
  } catch {
    /* quota / private mode — drafts just don't persist */
  }
}

function safeRemove(key: string): void {
  try {
    window.localStorage.removeItem(key)
  } catch {
    /* ignore */
  }
}

/** Persist a draft for the given program (null/undefined = general). */
export function saveWorkshopDraft(
  prefix: string,
  programId: string | null | undefined,
  draft: unknown,
): void {
  const key = storageKey(prefix, programId)
  safeSet(key, JSON.stringify(draft))
  safeSet(`${prefix}:last`, key)
}

/** Remove the draft for the given program; clears the last-pointer if it pointed here. */
export function clearWorkshopDraft(prefix: string, programId: string | null | undefined): void {
  const key = storageKey(prefix, programId)
  safeRemove(key)
  if (safeGet(`${prefix}:last`) === key) safeRemove(`${prefix}:last`)
}

/**
 * Load the most recently saved draft for this panel (following the `:last`
 * pointer, falling back to the general draft). Returns null when nothing is
 * stored or the payload doesn't parse to an object.
 */
export function loadLastWorkshopDraft<T extends object>(prefix: string): T | null {
  const key = safeGet(`${prefix}:last`) ?? storageKey(prefix, null)
  const raw = safeGet(key)
  if (!raw) return null
  try {
    const parsed = JSON.parse(raw)
    return parsed && typeof parsed === 'object' ? (parsed as T) : null
  } catch {
    return null
  }
}
