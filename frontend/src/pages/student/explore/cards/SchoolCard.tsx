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
  const programNames = school.program_names ?? []
  return (
    <div
      onClick={onClick}
      className="bg-card rounded-lg border border-border hover:shadow-md hover:-translate-y-0.5 transition-all duration-200 ease-out overflow-hidden cursor-pointer flex flex-col group/card"
    >
      <div className="flex-1 px-5 pt-4 pb-3">
        <h3 className="text-[15px] font-bold text-foreground leading-snug mb-1">{school.name}</h3>

        <div className="flex items-center gap-1.5 text-xs text-muted-foreground mb-3">
          <BookOpen size={12} className="text-secondary flex-shrink-0" />
          <span><span className="font-semibold text-foreground">{school.program_count}</span> programs</span>
          <span className="text-muted-foreground/40">·</span>
          <span className="truncate">{institutionName}</span>
        </div>

        {school.description_text && (
          <p className="text-[12px] text-muted-foreground leading-relaxed line-clamp-2 mb-3">
            {school.description_text}
          </p>
        )}

        {programNames.length > 0 && (
          <div className="flex flex-wrap gap-1">
            {programNames.slice(0, 6).map(name => (
              <span key={name} className="px-2 py-0.5 text-[10px] rounded-md bg-muted text-muted-foreground border border-border/50 truncate max-w-[120px]">
                {name}
              </span>
            ))}
            {programNames.length > 6 && (
              <span className="px-2 py-0.5 text-[10px] rounded-md bg-muted text-muted-foreground border border-border/50 font-medium">
                +{programNames.length - 6} more
              </span>
            )}
          </div>
        )}
      </div>

      <div className="flex items-center border-t border-border mt-auto px-5 py-2.5">
        <span className="text-xs font-semibold text-secondary flex-1">View programs</span>
        <ChevronRight size={16} className="text-secondary group-hover/card:translate-x-0.5 transition-transform" />
      </div>
    </div>
  )
}
