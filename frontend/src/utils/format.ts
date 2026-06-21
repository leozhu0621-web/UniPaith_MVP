import { format, formatDistanceToNow, parseISO } from 'date-fns'

// A malformed ISO string makes parseISO return an Invalid Date, and date-fns
// format()/formatDistanceToNow() THROW on that — which would crash the whole
// render tree. Guard every formatter so bad data degrades to a dash, not a crash.
function valid(iso: string): Date | null {
  const d = parseISO(iso)
  return isNaN(d.getTime()) ? null : d
}

export function formatDate(iso: string | null | undefined): string {
  if (!iso) return '—'
  const d = valid(iso)
  return d ? format(d, 'MMM d, yyyy') : '—'
}

export function formatDateTime(iso: string | null | undefined): string {
  if (!iso) return '—'
  const d = valid(iso)
  return d ? format(d, 'MMM d, yyyy h:mm a') : '—'
}

export function formatRelative(iso: string | null | undefined): string {
  if (!iso) return '—'
  const d = valid(iso)
  return d ? formatDistanceToNow(d, { addSuffix: true }) : '—'
}

export function formatCurrency(amount: number | null | undefined): string {
  if (amount == null) return '—'
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    maximumFractionDigits: 0,
  }).format(amount)
}

export function formatPercent(value: number | null | undefined, decimals = 0): string {
  if (value == null) return '—'
  return `${(value * 100).toFixed(decimals)}%`
}

export function formatScore(score: number | null | undefined): string {
  if (score == null) return '—'
  // Scores are stored as 0-1 decimals; display as percentage
  const pct = score <= 1 ? score * 100 : score
  return `${Math.round(pct)}%`
}

export function formatFileSize(bytes: number | null | undefined): string {
  if (bytes == null) return '—'
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

export function initials(name: string | null | undefined): string {
  if (!name) return '?'
  return name
    .split(' ')
    .map(p => p[0])
    .filter(Boolean)
    .slice(0, 2)
    .join('')
    .toUpperCase()
}
