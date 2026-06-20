import { Link } from 'react-router-dom'
import { MapPin, BellPlus, BellRing, ChevronRight, Trophy, BookOpen } from 'lucide-react'
import { classifyInstitution } from '../shared/classifyInstitution'
import { cardLinkClick, CARD_LINK_OVERLAY } from '../shared/cardLink'

interface UniversityData {
  id: string
  name: string
  country: string
  city?: string | null
  region?: string | null
  type?: string | null
  ownership?: string | null
  carnegie_classification?: string | null
  logo_url?: string | null
  program_count?: number
  acceptance_rate?: number | null
  us_news_rank?: number | null
}

interface Props {
  institution: UniversityData
  onClick: () => void
  following?: boolean
  onToggleFollow?: () => void
}

// Dense list-row variant of UniversityCard (browse grid/list toggle) — one line
// per university for fast scanning. Same stretched-link pattern as the card:
// the name <Link> overlays the row, Follow stays a raised sibling button.
export default function UniversityListRow({ institution: inst, onClick, following, onToggleFollow }: Props) {
  const classification = classifyInstitution({
    description_text: null,
    type: inst.type,
    ownership: inst.ownership,
    carnegie_classification: inst.carnegie_classification,
  })
  const locationStr = `${inst.city ? inst.city + ', ' : ''}${inst.region ? inst.region + ' · ' : ''}${inst.country}`
  const rank = inst.us_news_rank != null && inst.us_news_rank > 0 ? inst.us_news_rank : null
  const acceptancePct =
    inst.acceptance_rate != null && inst.acceptance_rate > 0
      ? Math.round(inst.acceptance_rate * (inst.acceptance_rate <= 1 ? 100 : 1))
      : null
  const programs = inst.program_count ?? 0

  return (
    <div className="relative group/row flex items-center gap-3 bg-card border border-border rounded-lg px-4 py-3 elev-subtle hover-lift hover:elev-raised">
      {inst.logo_url && (
        <img
          src={inst.logo_url}
          alt=""
          aria-hidden="true"
          loading="lazy"
          className="w-9 h-9 object-contain flex-shrink-0"
          onError={e => {
            ;(e.currentTarget as HTMLImageElement).style.display = 'none'
          }}
        />
      )}

      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <h3 className="text-sm font-semibold text-foreground truncate">
            <Link to={`/s/institutions/${inst.id}`} onClick={cardLinkClick(onClick)} className={CARD_LINK_OVERLAY}>
              {inst.name}
            </Link>
          </h3>
          {classification.code !== 'other' && (
            <span className="hidden md:inline text-[10px] font-semibold uppercase tracking-[0.14em] text-secondary flex-shrink-0">
              {classification.label}
            </span>
          )}
        </div>
        <div className="flex items-center gap-1.5 mt-0.5 text-xs text-muted-foreground">
          <MapPin size={11} className="flex-shrink-0" />
          <span className="truncate">{locationStr}</span>
        </div>
      </div>

      {/* Compact stat cluster — display-only, hidden on narrow screens. */}
      <div className="hidden sm:flex items-center gap-3 text-xs text-muted-foreground flex-shrink-0">
        {rank != null && (
          <span className="inline-flex items-center gap-1" title="US News rank">
            <Trophy size={12} className={rank === 1 ? 'text-primary' : 'text-muted-foreground'} />#{rank}
          </span>
        )}
        {acceptancePct != null && <span title="Acceptance rate">{acceptancePct}% accepted</span>}
        {programs > 0 && (
          <span className="inline-flex items-center gap-1" title="Programs">
            <BookOpen size={12} />
            {programs}
          </span>
        )}
      </div>

      {onToggleFollow && (
        <button
          onClick={e => { e.preventDefault(); e.stopPropagation(); onToggleFollow() }}
          aria-pressed={!!following}
          aria-label={following ? 'Following' : 'Follow'}
          className={`relative z-10 inline-flex items-center gap-1 px-2 py-1.5 text-xs font-semibold transition-colors flex-shrink-0 ${
            following ? 'text-muted-foreground hover:text-foreground' : 'text-secondary hover:underline'
          }`}
        >
          {following ? <BellRing size={13} /> : <BellPlus size={13} />}
          <span className="hidden lg:inline">{following ? 'Following' : 'Follow'}</span>
        </button>
      )}

      <ChevronRight size={16} className="text-secondary flex-shrink-0 group-hover/row:translate-x-0.5 transition-transform" />
    </div>
  )
}
