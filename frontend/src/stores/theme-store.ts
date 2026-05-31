import { create } from 'zustand'

// Spec 21 §2.3 — theme + accessibility preferences. The dark palette is fully
// defined in index.css (.dark CSS variables); this store just toggles the class
// + data-* attributes on <html> and persists locally. The no-FOUC init script
// in index.html applies the same values before first paint.

export type Theme = 'light' | 'dark' | 'system'
export type FontSize = 'sm' | 'md' | 'lg' | 'xl'

const LS = {
  theme: 'unipaith_theme',
  fontSize: 'unipaith_font_size',
  dyslexia: 'unipaith_dyslexia',
  reduceMotion: 'unipaith_reduce_motion',
} as const

function ls(key: string): string | null {
  try {
    return localStorage.getItem(key)
  } catch {
    return null
  }
}

function setLs(key: string, value: string | null) {
  try {
    if (value === null) localStorage.removeItem(key)
    else localStorage.setItem(key, value)
  } catch {
    /* private mode / SSR — ignore */
  }
}

function prefersDark(): boolean {
  return typeof window !== 'undefined' && !!window.matchMedia?.('(prefers-color-scheme: dark)').matches
}

export function isDark(theme: Theme): boolean {
  return theme === 'dark' || (theme === 'system' && prefersDark())
}

interface ThemeApplyState {
  theme: Theme
  fontSize: FontSize
  dyslexia: boolean
  reduceMotion: boolean
}

function apply(state: ThemeApplyState) {
  if (typeof document === 'undefined') return
  const root = document.documentElement
  const dark = isDark(state.theme)
  root.classList.toggle('dark', dark)
  root.setAttribute('data-font-size', state.fontSize)
  if (state.dyslexia) root.setAttribute('data-dyslexia', '')
  else root.removeAttribute('data-dyslexia')
  if (state.reduceMotion) root.setAttribute('data-reduce-motion', '')
  else root.removeAttribute('data-reduce-motion')
  // Keep the browser chrome (status bar / address bar) in sync.
  const meta = document.querySelector('meta[name="theme-color"]:not([media])')
  if (meta) meta.setAttribute('content', dark ? '#0A1428' : '#FCFAF2')
}

interface ThemeState extends ThemeApplyState {
  setTheme: (t: Theme) => void
  setFontSize: (f: FontSize) => void
  setDyslexia: (b: boolean) => void
  setReduceMotion: (b: boolean) => void
  /** Sync from the server's saved settings without fighting local persistence. */
  hydrate: (p: Partial<ThemeApplyState>) => void
}

function readInitial(): ThemeApplyState {
  const theme = (ls(LS.theme) as Theme) || 'system'
  const fontSize = (ls(LS.fontSize) as FontSize) || 'md'
  return {
    theme: (['light', 'dark', 'system'] as const).includes(theme) ? theme : 'system',
    fontSize: (['sm', 'md', 'lg', 'xl'] as const).includes(fontSize) ? fontSize : 'md',
    dyslexia: ls(LS.dyslexia) === '1',
    reduceMotion: ls(LS.reduceMotion) === '1',
  }
}

export const useThemeStore = create<ThemeState>((set, get) => ({
  ...readInitial(),

  setTheme: (theme) => {
    setLs(LS.theme, theme)
    set({ theme })
    apply({ ...get(), theme })
  },
  setFontSize: (fontSize) => {
    setLs(LS.fontSize, fontSize)
    set({ fontSize })
    apply({ ...get(), fontSize })
  },
  setDyslexia: (dyslexia) => {
    setLs(LS.dyslexia, dyslexia ? '1' : null)
    set({ dyslexia })
    apply({ ...get(), dyslexia })
  },
  setReduceMotion: (reduceMotion) => {
    setLs(LS.reduceMotion, reduceMotion ? '1' : null)
    set({ reduceMotion })
    apply({ ...get(), reduceMotion })
  },
  hydrate: (p) => {
    const next = { ...get(), ...p }
    if (p.theme !== undefined) setLs(LS.theme, p.theme)
    if (p.fontSize !== undefined) setLs(LS.fontSize, p.fontSize)
    if (p.dyslexia !== undefined) setLs(LS.dyslexia, p.dyslexia ? '1' : null)
    if (p.reduceMotion !== undefined) setLs(LS.reduceMotion, p.reduceMotion ? '1' : null)
    set(next)
    apply(next)
  },
}))

/** Apply persisted prefs at startup + react to OS theme changes when in `system`. */
export function initTheme() {
  const state = useThemeStore.getState()
  apply(state)
  if (typeof window !== 'undefined' && window.matchMedia) {
    const mq = window.matchMedia('(prefers-color-scheme: dark)')
    const onChange = () => {
      if (useThemeStore.getState().theme === 'system') apply(useThemeStore.getState())
    }
    if (mq.addEventListener) mq.addEventListener('change', onChange)
    else mq.addListener?.(onChange)
  }
}
