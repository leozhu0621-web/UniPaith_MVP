// Canonical UniPaith wordmark — single source of truth.
// Spec/01-brand-tokens.md §7.1 / Brand Materials/wordmark-*.svg.
// Europa Regular 400, −1.2 tracking. Caps (U, P) in sunlit gold; lowercase in
// cobalt (light surface) or warm cream (dark surface). Never re-spaced, never
// emboldened, never recolored. Below ~80px wide, prefer the UP monogram.

type WordmarkProps = {
  /** Tailwind sizing/utility classes. Height drives the scale. */
  className?: string
  /** `light` = cobalt lowercase (on light surfaces); `dark` = cream lowercase (on dark). */
  variant?: 'light' | 'dark'
  title?: string
}

export default function Wordmark({
  className = 'h-7 w-auto',
  variant = 'light',
  title = 'UniPaith',
}: WordmarkProps) {
  const lowercase = variant === 'dark' ? '#F5F1E8' : '#2A6BD4'
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
