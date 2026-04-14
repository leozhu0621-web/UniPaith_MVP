import { GraduationCap, MapPin, BookOpen, ChevronRight } from 'lucide-react'

interface Props {
  institution: {
    id: string
    name: string
    country: string
    city?: string | null
    type?: string | null
    program_count?: number
  }
  onView: () => void
}

export default function SchoolCard({ institution, onView }: Props) {
  return (
    <div
      onClick={onView}
      className="bg-white rounded-xl border border-divider hover:shadow-md transition-shadow overflow-hidden cursor-pointer"
    >
      <div className="flex items-center gap-4 p-4">
        {/* School avatar */}
        <div className="w-14 h-14 rounded-xl bg-school-mist flex items-center justify-center flex-shrink-0">
          <GraduationCap size={24} className="text-school" />
        </div>

        {/* Info */}
        <div className="flex-1 min-w-0">
          <h3 className="text-sm font-bold text-student-ink truncate">{institution.name}</h3>
          <p className="text-xs text-student-text flex items-center gap-1 mt-0.5">
            <MapPin size={10} />
            {institution.city ? `${institution.city}, ` : ''}{institution.country}
          </p>
          <div className="flex items-center gap-3 mt-1.5">
            {institution.type && (
              <span className="px-2 py-0.5 text-[10px] font-medium rounded-full bg-school-mist text-school">
                {institution.type}
              </span>
            )}
            {institution.program_count != null && institution.program_count > 0 && (
              <span className="text-[10px] text-student-text flex items-center gap-0.5">
                <BookOpen size={9} /> {institution.program_count} program{institution.program_count !== 1 ? 's' : ''}
              </span>
            )}
          </div>
        </div>

        {/* Arrow */}
        <ChevronRight size={16} className="text-student-text flex-shrink-0" />
      </div>
    </div>
  )
}
