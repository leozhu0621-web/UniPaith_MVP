interface Props {
  score: number // 0-1
  tier: number // 0-3
  size?: number
}

const TIER_COLORS: Record<number, { ring: string; text: string; label: string; bg: string }> = {
  3: { ring: 'stroke-emerald-500', text: 'text-emerald-700', label: 'Strong Fit', bg: 'bg-emerald-50' },
  2: { ring: 'stroke-blue-500', text: 'text-blue-700', label: 'Good Fit', bg: 'bg-blue-50' },
  1: { ring: 'stroke-amber-500', text: 'text-amber-700', label: 'Stretch', bg: 'bg-amber-50' },
  0: { ring: 'stroke-red-400', text: 'text-red-700', label: 'Reach', bg: 'bg-red-50' },
}

export default function MatchRing({ score, tier, size = 72 }: Props) {
  const pct = Math.round(score * 100)
  const color = TIER_COLORS[tier] ?? TIER_COLORS[0]
  const radius = (size - 10) / 2
  const circumference = 2 * Math.PI * radius
  const dashOffset = circumference * (1 - score)

  return (
    <div className={`flex items-center gap-3 px-3 py-2 rounded-xl ${color.bg} border border-divider`}>
      <div className="relative" style={{ width: size, height: size }}>
        <svg width={size} height={size} className="-rotate-90">
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke="currentColor"
            strokeWidth="5"
            className="text-slate-200"
          />
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke="currentColor"
            strokeWidth="5"
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={dashOffset}
            className={color.ring}
            style={{ transition: 'stroke-dashoffset 0.8s ease-out' }}
          />
        </svg>
        <div className="absolute inset-0 flex items-center justify-center">
          <span className={`text-lg font-bold ${color.text}`}>{pct}%</span>
        </div>
      </div>
      <div>
        <p className="text-[10px] font-semibold text-student-text uppercase tracking-wider">Your Match</p>
        <p className={`text-sm font-bold ${color.text}`}>{color.label}</p>
      </div>
    </div>
  )
}
