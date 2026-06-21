import { test, expect } from 'vitest'
import { formatDate, formatDateTime, formatRelative } from '../utils/format'

test('date formatters return a dash for empty input', () => {
  expect(formatDate(null)).toBe('—')
  expect(formatDateTime(undefined)).toBe('—')
  expect(formatRelative('')).toBe('—')
})

test('date formatters degrade to a dash on a malformed string instead of throwing', () => {
  // date-fns format()/formatDistanceToNow() throw on an Invalid Date — a
  // malformed deadline must not crash the render tree.
  expect(() => formatDate('not-a-date')).not.toThrow()
  expect(formatDate('not-a-date')).toBe('—')
  expect(formatDateTime('2026-13-99')).toBe('—')
  expect(formatRelative('garbage')).toBe('—')
})

test('date formatters render a valid ISO date', () => {
  expect(formatDate('2026-03-05')).toBe('Mar 5, 2026')
})
