/** Safe string for user-facing error toasts */
export function errorMessage(e: unknown): string {
  if (e instanceof Error) return e.message
  return String(e)
}
