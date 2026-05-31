import { describe, it, expect, beforeEach } from 'vitest'
import { useThemeStore, isDark } from '../stores/theme-store'

// Spec 21 §2.3 — theme store drives the <html> class + data-* attributes and
// persists to localStorage. The full .dark palette is in index.css.

describe('theme-store', () => {
  const KEYS = ['unipaith_theme', 'unipaith_font_size', 'unipaith_dyslexia', 'unipaith_reduce_motion']
  beforeEach(() => {
    KEYS.forEach(k => {
      try {
        localStorage.removeItem(k)
      } catch {
        /* ignore */
      }
    })
    document.documentElement.className = ''
    document.documentElement.removeAttribute('data-font-size')
    document.documentElement.removeAttribute('data-dyslexia')
    document.documentElement.removeAttribute('data-reduce-motion')
  })

  it('toggles the dark class on <html>', () => {
    useThemeStore.getState().setTheme('dark')
    expect(document.documentElement.classList.contains('dark')).toBe(true)

    useThemeStore.getState().setTheme('light')
    expect(document.documentElement.classList.contains('dark')).toBe(false)
  })

  it('applies font size as a data attribute', () => {
    useThemeStore.getState().setFontSize('lg')
    expect(document.documentElement.getAttribute('data-font-size')).toBe('lg')
  })

  it('toggles dyslexia + reduced-motion attributes', () => {
    useThemeStore.getState().setDyslexia(true)
    expect(document.documentElement.hasAttribute('data-dyslexia')).toBe(true)

    useThemeStore.getState().setReduceMotion(true)
    expect(document.documentElement.hasAttribute('data-reduce-motion')).toBe(true)

    useThemeStore.getState().setDyslexia(false)
    expect(document.documentElement.hasAttribute('data-dyslexia')).toBe(false)
  })

  it('hydrate() applies server values', () => {
    useThemeStore.getState().hydrate({ theme: 'dark', fontSize: 'xl', dyslexia: true, reduceMotion: false })
    expect(document.documentElement.classList.contains('dark')).toBe(true)
    expect(document.documentElement.getAttribute('data-font-size')).toBe('xl')
    expect(document.documentElement.hasAttribute('data-dyslexia')).toBe(true)
  })

  it('isDark resolves explicit themes', () => {
    expect(isDark('dark')).toBe(true)
    expect(isDark('light')).toBe(false)
  })
})
