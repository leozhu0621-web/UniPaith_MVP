import { formatCurrency } from '../../../../utils/format'
import { DEGREE_LABELS } from '../../../../utils/constants'
import type { ProgramSummary, MatchResult } from '../../../../types'
import {
  Bookmark, BookmarkCheck, MapPin, Clock, DollarSign,
  Users, GraduationCap, TrendingUp, ArrowRightLeft, MessageSquare,
} from 'lucide-react'

function fitLabel(tier: number) {
  if (tier >= 3) return { text: 'Strong Fit', color: 'text-emerald-700', bg: 'bg-emerald-50 border-emerald-200' }
  if (tier >= 2) return { text: 'Good Fit', color: 'text-blue-700', bg: 'bg-blue-50 border-blue-200' }
  return { text: 'Reach', color: 'text-amber-700', bg: 'bg-amber-50 border-amber-200' }
}

interface Props {
  program: ProgramSummary
  saved: boolean
  match?: MatchResult
  comparing?: boolean
  onSave: () => void
  onCompare?: () => void
  onAskCounselor?: () => void
  onView: () => void
}

export default function ProgramCard({ program, saved, match, comparing, onSave, onCompare, onAskCounselor, onView }: Props) {
  const degree = DEGREE_LABELS[program.degree_type] || program.degree_type
  const fit = match ? fitLabel(match.match_tier) : null
  const imgUrl = program.institution_image_url || program.institution_logo_url

  return (
    <div className="bg-white rounded-xl border border-divider hover:shadow-lg transition-all overflow-hidden flex flex-col">
      {/* Image area */}
      <div className="relative h-36 bg-student-mist cursor-pointer overflow-hidden" onClick={onView}>
        {imgUrl ? (
          <img
            src={imgUrl}
            alt={program.program_name}
            className="w-full h-full object-cover"
            onError={e => {
              e.currentTarget.style.display = 'none'
              e.currentTarget.parentElement!.classList.add('flex', 'items-center', 'justify-center')
              const icon = document.createElement('div')
              icon.innerHTML = '<span style="font-size:32px;opacity:0.3">🎓</span>'
              e.currentTarget.parentElement!.appendChild(icon)
            }}
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center">
            <GraduationCap size={32} className="text-student/20" />
          </div>
        )}

        {/* Fit badge */}
        {fit && (
          <span className={`absolute top-2 right-2 px-2 py-0.5 text-[10px] font-bold rounded-full border ${fit.bg} ${fit.color}`}>
            {fit.text}
          </span>
        )}

        {/* Degree pill */}
        <span className="absolute bottom-2 left-2 px-2 py-0.5 text-[10px] font-semibold rounded-full bg-black/40 text-white backdrop-blur-sm">
          {degree}
        </span>
      </div>

      {/* Content */}
      <div className="flex-1 px-4 pt-3 pb-2 cursor-pointer" onClick={onView}>
        <h3 className="text-sm font-bold text-student-ink leading-tight mb-1 line-clamp-2">{program.program_name}</h3>
        <div className="flex items-center gap-1.5 text-xs text-student-text mb-2">
          {program.institution_logo_url && (
            <img src={program.institution_logo_url} alt="" className="w-4 h-4 rounded-sm object-contain" onError={e => (e.currentTarget.style.display = 'none')} />
          )}
          <span className="truncate">{program.institution_name}</span>
          <span className="text-student-text/50">·</span>
          <MapPin size={9} className="flex-shrink-0" />
          <span className="truncate">{program.institution_city || program.institution_country}</span>
        </div>

        {/* Stats row — only show what exists */}
        <div className="flex flex-wrap gap-x-3 gap-y-1 text-[10px] text-student-text">
          {program.tuition != null && (
            <span className="flex items-center gap-0.5"><DollarSign size={9} /> {formatCurrency(program.tuition)}</span>
          )}
          {program.median_salary != null && (
            <span className="flex items-center gap-0.5"><TrendingUp size={9} /> {formatCurrency(program.median_salary)}</span>
          )}
          {program.employment_rate != null && (
            <span className="flex items-center gap-0.5"><Users size={9} /> {Math.round(program.employment_rate * 100)}%</span>
          )}
          {program.acceptance_rate != null && (
            <span className="flex items-center gap-0.5"><GraduationCap size={9} /> {Math.round(program.acceptance_rate * 100)}%</span>
          )}
          {program.duration_months != null && (
            <span className="flex items-center gap-0.5"><Clock size={9} /> {program.duration_months}mo</span>
          )}
        </div>
      </div>

      {/* Action bar */}
      <div className="flex items-center border-t border-divider mt-auto">
        <button onClick={e => { e.stopPropagation(); onSave() }} className={`flex-1 flex items-center justify-center gap-1 py-2 text-[11px] font-medium transition-colors ${saved ? 'text-student bg-student-mist' : 'text-student-text hover:bg-student-mist hover:text-student-ink'}`}>
          {saved ? <BookmarkCheck size={12} /> : <Bookmark size={12} />}
          {saved ? 'Saved' : 'Save'}
        </button>
        {onCompare && (
          <>
            <div className="w-px h-5 bg-divider" />
            <button onClick={e => { e.stopPropagation(); onCompare() }} className={`flex-1 flex items-center justify-center gap-1 py-2 text-[11px] font-medium transition-colors ${comparing ? 'text-student bg-student-mist' : 'text-student-text hover:bg-student-mist hover:text-student-ink'}`}>
              <ArrowRightLeft size={12} />
              Compare
            </button>
          </>
        )}
        {onAskCounselor && (
          <>
            <div className="w-px h-5 bg-divider" />
            <button onClick={e => { e.stopPropagation(); onAskCounselor() }} className="flex-1 flex items-center justify-center gap-1 py-2 text-[11px] font-medium text-gold hover:bg-gold-soft transition-colors">
              <MessageSquare size={12} />
              Ask AI
            </button>
          </>
        )}
      </div>
    </div>
  )
}
