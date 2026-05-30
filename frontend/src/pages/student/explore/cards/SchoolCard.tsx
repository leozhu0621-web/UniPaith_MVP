import { BookOpen, ChevronRight } from 'lucide-react'
import type { SchoolSummary } from '../../../../types'

interface Props {
  school: SchoolSummary
  institutionName: string
  onClick: () => void
}

// Editorial school-within-institution card — text-driven, duotone. No per-name
// rainbow palette, no gradient/image header (brand: gold punctuation only).
export default function SchoolCard({ school, institutionName, onClick }: Props) {
  return (
    <div
      onClick={onClick}
      className="bg-white rounded-lg border border-stone hover:shadow-md hover:-translate-y-0.5 transition-all duration-200 ease-out overflow-hidden cursor-pointer flex flex-col group/card"
    >
      <div className="flex-1 px-5 pt-4 pb-3">
        <h3 className="text-[15px] font-bold text-charcoal leading-snug mb-1">{school.name}</h3>

        <div className="flex items-center gap-1.5 text-xs text-slate mb-3">
          <BookOpen size={12} className="text-cobalt flex-shrink-0" />
          <span><span className="font-semibold text-charcoal">{school.program_count}</span> programs</span>
          <span className="text-slate/40">·</span>
          <span className="truncate">{institutionName}</span>
        </div>

        {school.description_text && (
          <p className="text-[12px] text-slate leading-relaxed line-clamp-2 mb-3">
            {school.description_text}
          </p>
        )}

        {school.program_names.length > 0 && (
          <div className="flex flex-wrap gap-1">
            {school.program_names.slice(0, 6).map(name => (
              <span key={name} className="px-2 py-0.5 text-[10px] rounded-md bg-muted text-slate border border-stone/50 truncate max-w-[120px]">
                {name}
              </span>
            ))}
            {school.program_names.length > 6 && (
              <span className="px-2 py-0.5 text-[10px] rounded-md bg-muted text-slate border border-stone/50 font-medium">
                +{school.program_names.length - 6} more
              </span>
            )}
          </div>
        )}
      </div>

      <div className="flex items-center border-t border-divider mt-auto px-5 py-2.5">
        <span className="text-xs font-semibold text-cobalt flex-1">View programs</span>
        <ChevronRight size={16} className="text-cobalt group-hover/card:translate-x-0.5 transition-transform" />
      </div>
    </div>
  )
}
