/**
 * Shared UI copy (Spec 78 §8) — error/empty/offline strings in one place so the
 * student app speaks with one voice: plain, honest, no blame, always a next step.
 * Prefer these over ad-hoc inline strings in QueryError / empty states.
 */
export const COPY = {
  errLoad: "We couldn't load this.",
  errRetry: 'Try again',
  errGeneric: "We couldn't do that. Please try again.",
  offline: "You're offline. We'll reconnect automatically.",
  emptyGeneric: 'Nothing here yet.',
} as const
