// Safe in-app redirect target from a ?next= param (Spec/04 §9, §15).
// Guards against open redirects: only same-origin absolute paths ('/...'),
// never protocol-relative ('//evil.com'), backslash tricks, or external URLs.
export function safeNextPath(next: string | null | undefined): string | null {
  if (!next) return null
  if (!next.startsWith('/')) return null
  if (next.startsWith('//') || next.startsWith('/\\')) return null
  return next
}
