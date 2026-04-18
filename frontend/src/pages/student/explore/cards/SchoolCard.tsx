import { Building2, BookOpen, ChevronRight } from 'lucide-react'
import type { SchoolSummary } from '../../../../types'

// Deterministic color from school name
const SCHOOL_COLORS = [
  { bg: 'from-blue-500/10 to-indigo-500/5', accent: 'text-blue-700', border: 'border-blue-100' },
  { bg: 'from-emerald-500/10 to-teal-500/5', accent: 'text-emerald-700', border: 'border-emerald-100' },
  { bg: 'from-amber-500/10 to-orange-500/5', accent: 'text-amber-700', border: 'border-amber-100' },
  { bg: 'from-purple-500/10 to-violet-500/5', accent: 'text-purple-700', border: 'border-purple-100' },
  { bg: 'from-rose-500/10 to-pink-500/5', accent: 'text-rose-700', border: 'border-rose-100' },
  { bg: 'from-cyan-500/10 to-sky-500/5', accent: 'text-cyan-700', border: 'border-cyan-100' },
  { bg: 'from-lime-500/10 to-green-500/5', accent: 'text-lime-700', border: 'border-lime-100' },
  { bg: 'from-fuchsia-500/10 to-pink-500/5', accent: 'text-fuchsia-700', border: 'border-fuchsia-100' },
  { bg: 'from-stone-400/10 to-slate-400/5', accent: 'text-stone-700', border: 'border-stone-100' },
]

function schoolColor(name: string) {
  const hash = name.split('').reduce((a, c) => a + c.charCodeAt(0), 0)
  return SCHOOL_COLORS[hash % SCHOOL_COLORS.length]
}

interface Props {
  school: SchoolSummary
  institutionName: string
  onClick: () => void
}

export default function SchoolCard({ school, institutionName, onClick }: Props) {
  const color = schoolColor(school.name)

  return (
    <div
      onClick={onClick}
      className={`bg-white rounded-xl border ${color.border} hover:shadow-lg hover:scale-[1.005] hover:-translate-y-0.5 transition-all duration-200 ease-out overflow-hidden cursor-pointer flex flex-col group/card`}
    >
      {/* ── Header area (colored gradient instead of image) ── */}
      <div className={`relative h-28 bg-gradient-to-br ${color.bg} flex items-center justify-center overflow-hidden`}>
        {school.media_urls && Array.isArray(school.media_urls) && school.media_urls[0] ? (
          <img
            src={school.media_urls[0]}
            alt={school.name}
            className="w-full h-full object-cover"
            onError={e => (e.currentTarget.style.display = 'none')}
          />
        ) : (
          <Building2 size={40} className={`${color.accent} opacity-20`} />
        )}
      </div>

      {/* ── Content ── */}
      <div className="flex-1 px-4 pt-3 pb-3">
        <h3 className="text-[15px] font-bold text-student-ink leading-snug mb-1">{school.name}</h3>

        <div className="flex items-center gap-1.5 text-xs text-student-text mb-3">
          <BookOpen size={11} className="text-student flex-shrink-0" />
          <span><span className="font-semibold text-student-ink">{school.program_count}</span> programs</span>
          <span className="text-student-text/40">·</span>
          <span className="truncate">{institutionName}</span>
        </div>

        {/* Description if available */}
        {school.description_text && (
          <p className="text-[11px] text-student-text/80 leading-relaxed line-clamp-2 mb-3">
            {school.description_text}
          </p>
        )}

        {/* Program names as pills */}
        {school.program_names.length > 0 && (
          <div className="flex flex-wrap gap-1">
            {school.program_names.slice(0, 6).map(name => (
              <span key={name} className="px-2 py-0.5 text-[10px] rounded-md bg-slate-50 text-student-text truncate max-w-[120px]">
                {name}
              </span>
            ))}
            {school.program_names.length > 6 && (
              <span className="px-2 py-0.5 text-[10px] rounded-md bg-slate-50 text-student-text font-medium">
                +{school.program_names.length - 6} more
              </span>
            )}
          </div>
        )}
      </div>

      {/* ── Action ── */}
      <div className="flex items-center border-t border-divider mt-auto px-4 py-2.5">
        <span className={`text-xs font-medium ${color.accent} flex-1`}>View Programs</span>
        <ChevronRight size={16} className={`${color.accent} group-hover/card:translate-x-0.5 transition-transform`} />
      </div>
    </div>
  )
}
