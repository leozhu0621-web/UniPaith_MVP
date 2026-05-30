import { Building2, BookOpen, ChevronRight } from 'lucide-react'
import type { SchoolSummary } from '../../../../types'

/**
 * Editorial school card — Europa + Paper + Cobalt/Gold duotone.
 *
 * No technicolor palette: the brand is a strict gold/cobalt-on-paper
 * duotone (Spec/01 §1 — "no gradients", "yellow is punctuation, not fill").
 * The header is a flat paper-mist panel with a faint cobalt mark; a real
 * media image still wins when present.
 */
interface Props {
  school: SchoolSummary
  institutionName: string
  onClick: () => void
}

export default function SchoolCard({ school, institutionName, onClick }: Props) {
  const mediaImg =
    school.media_urls && Array.isArray(school.media_urls) ? school.media_urls[0] : null

  return (
    <div
      onClick={onClick}
      className="bg-white rounded-lg border border-stone/60 hover:shadow-raised hover:-translate-y-0.5 transition-all duration-base ease-brand-out overflow-hidden cursor-pointer flex flex-col group/card"
    >
      {/* ── Header — flat paper-mist panel, faint cobalt mark (no gradient) ── */}
      <div className="relative h-28 bg-student-mist border-b border-stone/40 flex items-center justify-center overflow-hidden">
        {mediaImg ? (
          <img
            src={mediaImg}
            alt={school.name}
            className="w-full h-full object-cover"
            onError={e => (e.currentTarget.style.display = 'none')}
          />
        ) : (
          <Building2 size={40} className="text-cobalt/20" />
        )}
      </div>

      {/* ── Content ── */}
      <div className="flex-1 px-4 pt-3 pb-3">
        <h3 className="text-[15px] font-bold text-charcoal leading-snug mb-1">{school.name}</h3>

        <div className="flex items-center gap-1.5 text-xs text-slate mb-3">
          <BookOpen size={11} className="text-cobalt flex-shrink-0" />
          <span><span className="font-semibold text-charcoal">{school.program_count}</span> programs</span>
          <span className="text-slate/40">·</span>
          <span className="truncate">{institutionName}</span>
        </div>

        {/* Description if available */}
        {school.description_text && (
          <p className="text-[11px] text-slate/80 leading-relaxed line-clamp-2 mb-3">
            {school.description_text}
          </p>
        )}

        {/* Program names as pills */}
        {school.program_names.length > 0 && (
          <div className="flex flex-wrap gap-1">
            {school.program_names.slice(0, 6).map(name => (
              <span key={name} className="px-2 py-0.5 text-[10px] rounded-sm bg-paper border border-stone/50 text-slate truncate max-w-[120px]">
                {name}
              </span>
            ))}
            {school.program_names.length > 6 && (
              <span className="px-2 py-0.5 text-[10px] rounded-sm bg-paper border border-stone/50 text-slate font-medium">
                +{school.program_names.length - 6} more
              </span>
            )}
          </div>
        )}
      </div>

      {/* ── Action ── */}
      <div className="flex items-center border-t border-stone/60 mt-auto px-4 py-2.5">
        <span className="text-xs font-bold text-cobalt flex-1">View Programs</span>
        <ChevronRight size={16} className="text-cobalt group-hover/card:translate-x-0.5 transition-transform" />
      </div>
    </div>
  )
}
