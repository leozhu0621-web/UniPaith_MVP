// Canonical UniPaith wordmark — single source of truth.
// Spec/01-brand-tokens.md §7.1 / Brand Materials/wordmark-*.svg.
// Europa Regular 400, −1.2 tracking. Caps (U, P) in sunlit gold;
// lowercase in cobalt on light, warm cream on dark. Never re-spaced,
// never emboldened, never recolored. Below ~80px wide, prefer the UP
// monogram.
//
// When variant is omitted, the component auto-detects the active theme
// via [data-theme="dark"] / .dark on <html>, so the same instance works
// on both surfaces.

import { useEffect, useState } from 'react'

type WordmarkProps = {
  /** Tailwind sizing/utility classes. Height drives the scale. */
  className?: string
  /** Force a variant. Omit to auto-detect from the active theme. */
  variant?: 'light' | 'dark' | 'auto'
  title?: string
}

function useThemeIsDark() {
  const [isDark, setIsDark] = useState(() => {
    if (typeof document === 'undefined') return false
    return (
      document.documentElement.classList.contains('dark') ||
      document.documentElement.getAttribute('data-theme') === 'dark'
    )
  })

  useEffect(() => {
    const el = document.documentElement
    const obs = new MutationObserver(() => {
      setIsDark(
        el.classList.contains('dark') || el.getAttribute('data-theme') === 'dark',
      )
    })
    obs.observe(el, { attributes: true, attributeFilter: ['class', 'data-theme'] })
    return () => obs.disconnect()
  }, [])

  return isDark
}

export default function Wordmark({
  className = 'h-7 w-auto',
  variant = 'auto',
  title = 'UniPaith',
}: WordmarkProps) {
  const isDark = useThemeIsDark()
  const resolved = variant === 'auto' ? (isDark ? 'dark' : 'light') : variant
  const lowercase = resolved === 'dark' ? '#F5F1E8' : '#2A6BD4'
  return (
    <svg viewBox="0 0 260 80" className={className} aria-label={title} role="img">
      <text
        x="17"
        y="58"
        fontFamily="europa, system-ui, -apple-system, 'Segoe UI', sans-serif"
        fontWeight="400"
        fontSize="56"
        letterSpacing="-1.2"
      >
        <tspan fill="#FFD60A">U</tspan>
        <tspan fill={lowercase}>ni</tspan>
        <tspan fill="#FFD60A">P</tspan>
        <tspan fill={lowercase}>aith</tspan>
      </text>
    </svg>
  )
}
