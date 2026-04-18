import { Sparkles, TrendingUp, Users, Target, BookOpen, Check } from 'lucide-react'

/**
 * MatchSummary — explains the match in WORDS, not a number.
 *
 * Replaces the old 40%-in-a-ring design. Students don't care what "40%"
 * means — they care WHY this program fits them. We surface 2–3 short
 * human-readable reasons derived from the score breakdown.
 */

type Tier = 1 | 2 | 3

interface Props {
  matchTier: number | null | undefined
  scoreBreakdown?: Record<string, number> | null
  onClick?: () => void
}

const TIER_STYLE: Record<Tier, {
  headline: string
  subtext: string
  bg: string
  border: string
  text: string
  chip: string
  accent: string
}> = {
  3: {
    headline: 'Strong Fit',
    subtext: 'Well aligned with you',
    bg: 'bg-emerald-50',
    border: 'border-emerald-200',
    text: 'text-emerald-800',
    chip: 'bg-white text-emerald-700 border-emerald-200',
    accent: 'text-emerald-600',
  },
  2: {
    headline: 'Good Fit',
    subtext: 'Worth a closer look',
    bg: 'bg-blue-50',
    border: 'border-blue-200',
    text: 'text-blue-800',
    chip: 'bg-white text-blue-700 border-blue-200',
    accent: 'text-blue-600',
  },
  1: {
    headline: 'Reach',
    subtext: 'Ambitious stretch',
    bg: 'bg-amber-50',
    border: 'border-amber-200',
    text: 'text-amber-800',
    chip: 'bg-white text-amber-700 border-amber-200',
    accent: 'text-amber-600',
  },
}

/** Map internal ML signal names to short human-readable reasons. */
const SIGNAL_TO_REASON: Record<string, { label: string; icon: any }> = {
  embedding_similarity:     { label: 'Interests align',  icon: Sparkles },
  collaborative_filtering:  { label: 'Peers love it',    icon: Users },
  pattern_affinity:         { label: 'Profile fit',      icon: Target },
  interaction_score:        { label: 'Active interest',  icon: TrendingUp },
  xgboost_score:            { label: 'Model confident',  icon: Check },
  knowledge_relevance:      { label: 'Goal aligned',     icon: BookOpen },
}

/** Fallback reasons by tier when we don't have a score breakdown. */
const TIER_DEFAULT_REASONS: Record<Tier, Array<{ label: string; icon: any }>> = {
  3: [
    { label: 'Interests align', icon: Sparkles },
    { label: 'Profile fit', icon: Target },
    { label: 'Within reach', icon: Check },
  ],
  2: [
    { label: 'Interests align', icon: Sparkles },
    { label: 'Worth exploring', icon: Target },
  ],
  1: [
    { label: 'Ambitious goal', icon: TrendingUp },
    { label: 'Standout application needed', icon: Sparkles },
  ],
}

function clampTier(t: number | null | undefined): Tier {
  if (!t || t <= 1) return 1
  if (t >= 3) return 3
  return 2
}

function pickReasons(breakdown: Record<string, number> | null | undefined, tier: Tier): Array<{ label: string; icon: any }> {
  if (!breakdown) return TIER_DEFAULT_REASONS[tier]

  // Filter for keys we know how to translate, rank by contribution
  const ranked = Object.entries(breakdown)
    .filter(([k]) => SIGNAL_TO_REASON[k])
    .sort((a, b) => (b[1] ?? 0) - (a[1] ?? 0))

  if (ranked.length === 0) return TIER_DEFAULT_REASONS[tier]

  // Pick top 3 positive contributors
  const picked = ranked
    .filter(([, v]) => v > 0)
    .slice(0, 3)
    .map(([k]) => SIGNAL_TO_REASON[k])

  return picked.length > 0 ? picked : TIER_DEFAULT_REASONS[tier]
}

export default function MatchSummary({ matchTier, scoreBreakdown, onClick }: Props) {
  if (matchTier == null) return null

  const tier = clampTier(matchTier)
  const style = TIER_STYLE[tier]
  const reasons = pickReasons(scoreBreakdown, tier)

  return (
    <button
      onClick={onClick}
      className={`text-left group rounded-xl border ${style.bg} ${style.border} px-4 py-3 transition-all hover:shadow-sm`}
      title="Click to see full match analysis"
    >
      {/* Headline */}
      <div className="flex items-center gap-1.5 mb-1">
        <Sparkles size={12} className={style.accent} />
        <p className={`text-[10px] uppercase tracking-wider font-bold ${style.accent}`}>Your Fit</p>
      </div>
      <h3 className={`text-[17px] font-bold leading-tight ${style.text}`}>{style.headline}</h3>
      <p className={`text-[11px] ${style.text}/70 mt-0.5`}>{style.subtext}</p>

      {/* Reasons as small chips */}
      <div className="flex flex-wrap gap-1 mt-2.5">
        {reasons.map((r, i) => (
          <span
            key={i}
            className={`inline-flex items-center gap-1 px-1.5 py-0.5 text-[10px] rounded-md border ${style.chip}`}
          >
            <r.icon size={9} />
            {r.label}
          </span>
        ))}
      </div>
    </button>
  )
}
