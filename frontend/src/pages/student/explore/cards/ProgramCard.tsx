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

const BANNER_GRADIENTS: Record<string, string> = {
  masters: 'from-student/90 to-student-hover/80',
  phd: 'from-indigo-600/90 to-indigo-800/80',
  bachelors: 'from-sky-500/90 to-sky-700/80',
  certificate: 'from-amber-500/90 to-amber-700/80',
  diploma: 'from-teal-500/90 to-teal-700/80',
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
  const gradient = BANNER_GRADIENTS[program.degree_type] || BANNER_GRADIENTS.masters
  const fit = match ? fitLabel(match.match_tier) : null
  const deadlineDate = program.application_deadline ? new Date(program.application_deadline) : null
  const daysLeft = deadlineDate ? Math.ceil((deadlineDate.getTime() - Date.now()) / 86400000) : null

  return (
    <div className="bg-white rounded-xl border border-divider hover:shadow-lg transition-all overflow-hidden">
      {/* Hero Banner */}
      <div className={`relative bg-gradient-to-r ${gradient} px-5 pt-5 pb-4 cursor-pointer`} onClick={onView}>
        {fit && (
          <span className={`absolute top-3 right-3 px-2.5 py-1 text-[10px] font-bold rounded-full border ${fit.bg} ${fit.color}`}>
            {fit.text}
          </span>
        )}
        <span className="inline-block px-2.5 py-0.5 text-[10px] font-semibold rounded-full bg-white/20 text-white backdrop-blur-sm mb-3">
          {degree}
          {program.delivery_format && ` · ${program.delivery_format.replace(/_/g, ' ')}`}
          {program.duration_months && ` · ${program.duration_months}mo`}
        </span>
        <h3 className="text-lg font-bold text-white leading-tight mb-1">{program.program_name}</h3>
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-md bg-white/20 backdrop-blur-sm flex items-center justify-center">
            <GraduationCap size={14} className="text-white" />
          </div>
          <div>
            <p className="text-sm font-medium text-white/95">{program.institution_name}</p>
            <p className="text-[10px] text-white/70 flex items-center gap-1">
              <MapPin size={8} />
              {program.institution_city ? `${program.institution_city}, ` : ''}{program.institution_country}
            </p>
          </div>
        </div>
      </div>

      {/* Stats — only show fields that have data */}
      {(() => {
        const stats: { icon: typeof DollarSign; label: string; value: string; urgent?: boolean }[] = []
        if (program.tuition != null) stats.push({ icon: DollarSign, label: 'Tuition', value: formatCurrency(program.tuition) })
        if (program.median_salary != null) stats.push({ icon: TrendingUp, label: 'Avg Salary', value: formatCurrency(program.median_salary) })
        if (program.employment_rate != null) stats.push({ icon: Users, label: 'Grad Rate', value: `${Math.round(program.employment_rate * 100)}%` })
        if (program.acceptance_rate != null) stats.push({ icon: GraduationCap, label: 'Accept', value: `${Math.round(program.acceptance_rate * 100)}%` })
        if (daysLeft != null && daysLeft >= 0) stats.push({ icon: Clock, label: 'Deadline', value: daysLeft === 0 ? 'Today' : `${daysLeft}d`, urgent: daysLeft <= 14 })
        else if (deadlineDate) stats.push({ icon: Clock, label: 'Deadline', value: deadlineDate.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }) })
        if (program.duration_months) stats.push({ icon: Clock, label: 'Duration', value: `${program.duration_months}mo` })

        if (stats.length === 0) return null
        return (
          <div className="divide-x divide-divider border-b border-divider" style={{ display: 'grid', gridTemplateColumns: `repeat(${Math.min(stats.length, 4)}, 1fr)` }}>
            {stats.slice(0, 4).map(s => (
              <div key={s.label} className="px-3 py-2.5 text-center">
                <p className="text-[10px] text-student-text mb-0.5 flex items-center justify-center gap-0.5"><s.icon size={9} /> {s.label}</p>
                <p className={`text-xs font-bold ${s.urgent ? 'text-red-600' : 'text-student-ink'}`}>{s.value}</p>
              </div>
            ))}
          </div>
        )
      })()}

      {/* Action Bar */}
      <div className="flex items-center divide-x divide-divider">
        <button onClick={e => { e.stopPropagation(); onSave() }} className={`flex-1 flex items-center justify-center gap-1.5 py-2.5 text-xs font-medium transition-colors ${saved ? 'text-student bg-student-mist' : 'text-student-text hover:bg-student-mist hover:text-student-ink'}`}>
          {saved ? <BookmarkCheck size={13} className="text-student" /> : <Bookmark size={13} />}
          {saved ? 'Saved' : 'Save'}
        </button>
        {onCompare && (
          <button onClick={e => { e.stopPropagation(); onCompare() }} className={`flex-1 flex items-center justify-center gap-1.5 py-2.5 text-xs font-medium transition-colors ${comparing ? 'text-student bg-student-mist' : 'text-student-text hover:bg-student-mist hover:text-student-ink'}`}>
            <ArrowRightLeft size={13} />
            {comparing ? 'Comparing' : 'Compare'}
          </button>
        )}
        {onAskCounselor && (
          <button onClick={e => { e.stopPropagation(); onAskCounselor() }} className="flex-1 flex items-center justify-center gap-1.5 py-2.5 text-xs font-medium text-gold hover:bg-gold-soft transition-colors">
            <MessageSquare size={13} />
            Ask Counselor
          </button>
        )}
      </div>
    </div>
  )
}
