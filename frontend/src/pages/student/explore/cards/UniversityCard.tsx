import type { ComponentType } from 'react'
import { Link } from 'react-router-dom'
import {
  MapPin, Users, Building2, BookOpen, BellPlus, BellRing, ChevronRight, Sprout,
  Trophy, GraduationCap,
} from 'lucide-react'
import { classifyInstitution, sizeBucket, formatSetting, SIZE_OPTIONS } from '../shared/classifyInstitution'
import { cardLinkClick, CARD_LINK_OVERLAY } from '../shared/cardLink'
import Badge from '../../../../components/ui/Badge'

interface UniversityData {
  id: string
  name: string
  country: string
  city?: string | null
  region?: string | null
  type?: string | null
  ownership?: string | null
  carnegie_classification?: string | null
  campus_setting?: string | null
  student_body_size?: number | null
  logo_url?: string | null
  image_url?: string | null
  image_credit?: string | null
  program_count?: number
  school_count?: number
  description_text?: string | null
  subjects_offered?: string[] | null
  top_industries?: string[] | null
  acceptance_rate?: number | null
  sat_avg?: number | null
  us_news_rank?: number | null
  median_earnings?: number | null
  graduation_rate?: number | null
  tuition_annual?: number | null
}

interface Props {
  institution: UniversityData
  onClick: () => void
  /** Spec 2026-06-12 §6.1 — grow the follow graph where discovery happens. */
  following?: boolean
  onToggleFollow?: () => void
}

// Editorial school card (Spec/02 §5, /14) with a campus-photo header that fades
// into the card background — the same gradient treatment as the detail-page hero
// (set 2026-06-12, supersedes the earlier text-only card rule). Falls back to the
// clean text header when the university has no photo.
export default function UniversityCard({ institution: inst, onClick, following, onToggleFollow }: Props) {
  const classification = classifyInstitution({
    description_text: inst.description_text,
    type: inst.type,
    ownership: inst.ownership,
    carnegie_classification: inst.carnegie_classification,
  })
  const settingLabel = formatSetting(inst.campus_setting)
  const size = sizeBucket(inst.student_body_size)
  const sizeLabel = size ? SIZE_OPTIONS.find(s => s.code === size)?.label ?? null : null
  const locationStr = `${inst.city ? inst.city + ', ' : ''}${inst.region ? inst.region + ' · ' : ''}${inst.country}`
  // Campus photo for the header banner — raster only (logos are SVG → skipped).
  const photo = inst.image_url && /\.(jpe?g|png|webp|avif)(\?|$)/i.test(inst.image_url) ? inst.image_url : null

  // Stat strip (UX-QA Part 2) — pure data rendered as compact visuals, display
  // only. Each field guards null so the strip shows only what's known.
  const rank = inst.us_news_rank != null && inst.us_news_rank > 0 ? inst.us_news_rank : null
  const acceptancePct =
    inst.acceptance_rate != null && inst.acceptance_rate > 0
      ? Math.round(inst.acceptance_rate * (inst.acceptance_rate <= 1 ? 100 : 1))
      : null
  const gradPct =
    inst.graduation_rate != null && inst.graduation_rate > 0
      ? Math.round(inst.graduation_rate * (inst.graduation_rate <= 1 ? 100 : 1))
      : null
  const hasStats = rank != null || acceptancePct != null || gradPct != null

  return (
    // Stretched-link card (Ship D §4): the title <Link> overlays the whole
    // card, so keyboard + cmd/ctrl-click work; the Follow button stays a
    // sibling <button> raised above the overlay (no nested-interactive).
    <div
      className="relative bg-card rounded-xl border border-border elev-subtle hover-lift hover:elev-raised overflow-hidden flex flex-col group/card"
    >
      {/* Header — TALLER campus photo fading into the card at its bottom edge;
          the identity block sits fully BELOW the fade so text never collides
          with the photo (user feedback 2026-06-12). Text-only fallback when no
          photo. */}
      {photo && (
        <div className="relative h-64">
          <img
            src={photo}
            alt=""
            aria-hidden="true"
            loading="lazy"
            className="absolute inset-0 h-full w-full object-cover"
            onError={e => {
              ;(e.currentTarget.parentElement as HTMLElement).style.display = 'none'
            }}
          />
          {/* Soft top scrim for the credit; full fade into the card by the
              bottom edge so the photo melts into the header underneath. */}
          <div
            className="absolute inset-0"
            style={{
              background:
                'linear-gradient(to bottom, rgba(10,18,36,0.38) 0%, rgba(10,18,36,0.06) 26%, rgba(10,18,36,0) 55%, hsl(var(--card)) 100%)',
            }}
          />
          {inst.image_credit && (
            <p
              className="absolute top-1 right-2 text-[9px] text-white/80"
              style={{ textShadow: '0 1px 2px rgba(0,0,0,0.55)' }}
              title="Campus photo credit"
            >
              {inst.image_credit}
            </p>
          )}
        </div>
      )}
      <div className={`px-5 pb-3 border-b border-border ${photo ? 'pt-1' : 'pt-5'}`}>
        <div className="flex items-start gap-3">
          {inst.logo_url && (
            <img
              src={inst.logo_url}
              alt={`${inst.name} logo`}
              loading="lazy"
              className="w-10 h-10 object-contain flex-shrink-0"
              onError={e => {
                ;(e.currentTarget as HTMLImageElement).style.display = 'none'
              }}
            />
          )}
          <div className="min-w-0 flex-1">
            {classification.code !== 'other' && (
              <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-secondary mb-1.5">
                {classification.label}
              </p>
            )}
            <h3 className="text-lg leading-tight font-bold text-foreground line-clamp-2 break-words">
              <Link
                to={`/s/institutions/${inst.id}`}
                onClick={cardLinkClick(onClick)}
                className={CARD_LINK_OVERLAY}
              >
                {inst.name}
              </Link>
            </h3>
            <div className="flex items-center gap-1.5 mt-1.5 text-xs text-muted-foreground">
              <MapPin size={12} className="flex-shrink-0" />
              <span className="truncate">{locationStr}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Body — facts + description. */}
      <div className="flex-1 px-5 pt-3 pb-4 flex flex-col">
        <div className="flex flex-wrap items-center gap-1.5 mb-3">
          {settingLabel && <FactPill icon={Sprout}>{settingLabel}</FactPill>}
          {sizeLabel && <FactPill icon={Users}>{sizeLabel}</FactPill>}
          {(inst.school_count ?? 0) > 0 && <FactPill icon={Building2}>{inst.school_count} schools</FactPill>}
          {(inst.program_count ?? 0) > 0 && <FactPill icon={BookOpen}>{inst.program_count} programs</FactPill>}
        </div>

        {/* Stat strip — rank · acceptance · grad rate, all display-only (UX-QA
            Part 2). The rank pill takes the earned-gold tint only at #1. */}
        {hasStats && (
          <div className="flex flex-wrap items-center gap-1.5 mb-3">
            {rank != null && (
              <span
                className={`inline-flex items-center gap-1 px-2 py-0.5 text-[11px] font-semibold rounded-md border ${
                  rank === 1
                    ? 'bg-primary/15 text-foreground border-primary/40'
                    : 'bg-muted text-foreground border-border/60'
                }`}
                title="US News rank"
              >
                <Trophy size={11} className={rank === 1 ? 'text-primary' : 'text-muted-foreground'} />
                #{rank}
              </span>
            )}
            {acceptancePct != null && (
              <span title="Acceptance rate" className="inline-flex">
                <Badge variant="info">{acceptancePct}% accepted</Badge>
              </span>
            )}
            {gradPct != null && <FactPill icon={GraduationCap}>{gradPct}% grad rate</FactPill>}
          </div>
        )}

        {inst.description_text && (
          <p className="text-[13px] text-muted-foreground leading-relaxed line-clamp-2">
            {inst.description_text}
          </p>
        )}
      </div>

      {/* Footer action. */}
      <div className="flex items-center border-t border-border mt-auto px-5 py-2.5">
        <span className="text-xs font-semibold text-secondary flex-1">View university</span>
        {onToggleFollow && (
          <button
            onClick={e => { e.preventDefault(); e.stopPropagation(); onToggleFollow() }}
            aria-pressed={!!following}
            className={`relative z-10 mr-3 inline-flex items-center gap-1 px-2 py-3 -my-3 -mx-2 text-xs font-semibold transition-colors ${
              following ? 'text-muted-foreground hover:text-foreground' : 'text-secondary hover:underline'
            }`}
          >
            {following ? <><BellRing size={12} /> Following</> : <><BellPlus size={12} /> Follow</>}
          </button>
        )}
        <ChevronRight size={16} className="text-secondary group-hover/card:translate-x-0.5 transition-transform" />
      </div>
    </div>
  )
}

function FactPill({ icon: Icon, children }: { icon: ComponentType<{ size?: number; className?: string }>; children: React.ReactNode }) {
  return (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 text-[11px] rounded-md bg-muted text-foreground border border-border/60">
      <Icon size={11} className="text-muted-foreground" />
      {children}
    </span>
  )
}
