import clsx from 'clsx'

// Spec 32 §10 — per-reviewer score slider, 0–5, cobalt fill with a gold fill at
// "Excellent" (max). Accessible (native range input → keyboard + screen reader),
// brand-tokened (no raw colors). The thumb + fill turn gold when the score hits
// the top of the scale.
const QUALITATIVE = ['Not scored', 'Poor', 'Fair', 'Good', 'Strong', 'Excellent']

interface RubricSliderProps {
  value: number | null
  min?: number
  max?: number
  onChange: (value: number) => void
  disabled?: boolean
  label?: string
  id?: string
}

export default function RubricSlider({
  value,
  max = 5,
  min = 0,
  onChange,
  disabled = false,
  label,
  id,
}: RubricSliderProps) {
  const v = value ?? 0
  const isMax = value === max && value != null
  const pct = max > 0 && value != null ? (v / max) * 100 : 0
  // Cobalt fill; gold once the reviewer marks the top of the scale (§10).
  // Fill keeps the brand gold/cobalt hex (computed into an inline gradient);
  // the unfilled track uses the --muted token so it tracks the dark theme.
  const fillColor = isMax ? '#FFD60A' : '#2A6BD4'
  const mutedTrack = 'hsl(var(--muted))'
  const trackBg = value == null
    ? mutedTrack
    : `linear-gradient(to right, ${fillColor} 0%, ${fillColor} ${pct}%, ${mutedTrack} ${pct}%, ${mutedTrack} 100%)`
  const qualitative = value == null ? QUALITATIVE[0] : (QUALITATIVE[Math.round(v)] ?? '')

  return (
    <div className="flex items-center gap-3">
      <input
        id={id}
        type="range"
        min={min}
        max={max}
        step={1}
        value={value ?? min}
        disabled={disabled}
        aria-label={label ? `${label} score` : 'Score'}
        aria-valuetext={value == null ? 'Not scored' : `${value} of ${max} — ${qualitative}`}
        onChange={(e) => onChange(Number(e.target.value))}
        style={{ background: trackBg }}
        className={clsx(
          'h-2 flex-1 cursor-pointer appearance-none rounded-full outline-none',
          'focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-1',
          disabled && 'cursor-not-allowed opacity-50',
          // Webkit thumb
          '[&::-webkit-slider-thumb]:h-4 [&::-webkit-slider-thumb]:w-4',
          '[&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:rounded-full',
          '[&::-webkit-slider-thumb]:border-2 [&::-webkit-slider-thumb]:border-card',
          '[&::-webkit-slider-thumb]:shadow [&::-webkit-slider-thumb]:transition-colors',
          isMax
            ? '[&::-webkit-slider-thumb]:bg-primary [&::-moz-range-thumb]:bg-primary'
            : '[&::-webkit-slider-thumb]:bg-secondary [&::-moz-range-thumb]:bg-secondary',
          // Firefox thumb
          '[&::-moz-range-thumb]:h-4 [&::-moz-range-thumb]:w-4 [&::-moz-range-thumb]:rounded-full',
          '[&::-moz-range-thumb]:border-2 [&::-moz-range-thumb]:border-card',
        )}
      />
      <div className="flex w-24 shrink-0 items-baseline gap-1">
        <span
          className={clsx(
            'text-sm font-semibold tabular-nums',
            value == null ? 'text-muted-foreground' : isMax ? 'text-primary' : 'text-secondary',
          )}
        >
          {value ?? '–'}
        </span>
        <span className="text-xs text-muted-foreground">/ {max}</span>
        {value != null && (
          <span className="ml-1 truncate text-[11px] text-muted-foreground">{qualitative}</span>
        )}
      </div>
    </div>
  )
}
