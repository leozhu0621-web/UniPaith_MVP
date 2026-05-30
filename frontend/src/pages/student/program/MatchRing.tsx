interface Props {
  score: number // 0-1
  tier: number // 0-3
  size?: number
}

// Duotone match ring — gold is the earned fit accent; lower tiers shift to
// cobalt / warning. No status-color rainbow (Spec/01 §1, /11 §10).
const TIER_COLORS: Record<number, { ring: string; text: string; label: string; bg: string }> = {
  3: { ring: 'stroke-student', text: 'text-charcoal', label: 'Strong fit', bg: 'bg-student/10' },
  2: { ring: 'stroke-cobalt', text: 'text-cobalt', label: 'Good fit', bg: 'bg-cobalt/10' },
  1: { ring: 'stroke-cobalt', text: 'text-cobalt', label: 'Stretch', bg: 'bg-cobalt/5' },
  0: { ring: 'stroke-warning', text: 'text-warning', label: 'Reach', bg: 'bg-warning-soft' },
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
            className="text-stone/50"
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
        <p className="text-[10px] font-semibold text-slate uppercase tracking-wider">Your match</p>
        <p className={`text-sm font-bold ${color.text}`}>{color.label}</p>
      </div>
    </div>
  )
}
