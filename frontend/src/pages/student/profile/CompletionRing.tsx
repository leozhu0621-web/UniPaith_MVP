/**
 * Completion ring — SVG donut, fill in --primary (gold), track in --border
 * (spec 10 §3). Brand rule: gold is punctuation; this is one of the few gold
 * accents on the page.
 */
export default function CompletionRing({
  value,
  size = 64,
  label,
}: {
  value: number
  size?: number
  label?: string
}) {
  const stroke = 6
  const r = (size - stroke) / 2 - 1
  const c = 2 * Math.PI * r
  const pct = Math.min(100, Math.max(0, value))
  const offset = c - (pct / 100) * c
  const center = size / 2
  return (
    <div className="relative shrink-0" style={{ width: size, height: size }}>
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} className="-rotate-90">
        <circle cx={center} cy={center} r={r} fill="none" stroke="hsl(var(--border))" strokeWidth={stroke} />
        <circle
          cx={center}
          cy={center}
          r={r}
          fill="none"
          stroke="hsl(var(--primary))"
          strokeWidth={stroke}
          strokeDasharray={c}
          strokeDashoffset={offset}
          strokeLinecap="round"
          className="transition-all duration-700"
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center leading-none">
        <span className="font-semibold text-charcoal" style={{ fontSize: size * 0.26 }}>
          {Math.round(pct)}%
        </span>
        {label && (
          <span className="text-slate mt-0.5" style={{ fontSize: Math.max(8, size * 0.13) }}>
            {label}
          </span>
        )}
      </div>
    </div>
  )
}
