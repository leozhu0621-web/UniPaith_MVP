import { format, formatDistanceToNow, parseISO } from 'date-fns'

export function formatDate(iso: string | null | undefined): string {
  if (!iso) return '—'
  return format(parseISO(iso), 'MMM d, yyyy')
}

export function formatDateTime(iso: string | null | undefined): string {
  if (!iso) return '—'
  return format(parseISO(iso), 'MMM d, yyyy h:mm a')
}

export function formatRelative(iso: string | null | undefined): string {
  if (!iso) return '—'
  return formatDistanceToNow(parseISO(iso), { addSuffix: true })
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
  return `${Math.round(score)}%`
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
