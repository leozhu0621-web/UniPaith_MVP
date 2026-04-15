import { formatCurrency } from '../../../../utils/format'
import { DEGREE_LABELS } from '../../../../utils/constants'
import type { ProgramSummary, MatchResult } from '../../../../types'
import {
  Bookmark, BookmarkCheck, DollarSign, GraduationCap,
  TrendingUp, Percent, ArrowRightLeft, MessageSquare,
  FileText,
} from 'lucide-react'

function fitLabel(tier: number) {
  if (tier >= 3) return { text: 'Strong Fit', color: 'text-emerald-700', bg: 'bg-emerald-50' }
  if (tier >= 2) return { text: 'Good Fit', color: 'text-blue-700', bg: 'bg-blue-50' }
  return { text: 'Reach', color: 'text-amber-700', bg: 'bg-amber-50' }
}

// Color based on degree type
const DEGREE_COLORS: Record<string, string> = {
  bachelors: 'from-student/10 to-student/5 border-student/15',
  masters: 'from-indigo-500/10 to-indigo-500/5 border-indigo-200',
  phd: 'from-purple-500/10 to-purple-500/5 border-purple-200',
  certificate: 'from-emerald-500/10 to-emerald-500/5 border-emerald-200',
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
  const headerColor = DEGREE_COLORS[program.degree_type] || DEGREE_COLORS.bachelors

  const acceptPct = program.acceptance_rate != null ? Math.round(program.acceptance_rate * 100) : null
  const gradPct = program.employment_rate != null ? Math.round(program.employment_rate * 100) : null

  return (
    <div className="bg-white rounded-xl border border-divider hover:shadow-lg hover:scale-[1.005] hover:-translate-y-0.5 transition-all duration-200 ease-out overflow-hidden flex flex-col group/card">
      {/* ── Colored header (no image) ── */}
      <div className={`relative px-4 pt-3 pb-2.5 bg-gradient-to-r ${headerColor} border-b cursor-pointer`} onClick={onView}>
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0 flex-1">
            <h3 className="text-[15px] font-bold text-student-ink leading-snug line-clamp-2">
              {program.program_name}
            </h3>
            <div className="flex items-center gap-2 mt-1">
              <span className="px-2 py-0.5 text-[10px] font-semibold rounded-md bg-white/80 text-student-ink">
                {degree}
              </span>
              {fit && (
                <span className={`px-2 py-0.5 text-[10px] font-bold rounded-md ${fit.bg} ${fit.color}`}>
                  {fit.text}
                </span>
              )}
            </div>
          </div>
          <button
            onClick={e => { e.stopPropagation(); onSave() }}
            className={`p-1.5 rounded-full transition-all duration-200 flex-shrink-0 ${
              saved ? 'bg-student text-white' : 'bg-white/60 text-student-text hover:bg-white hover:text-student-ink'
            }`}
          >
            {saved ? <BookmarkCheck size={14} /> : <Bookmark size={14} />}
          </button>
        </div>
      </div>

      {/* ── Content ── */}
      <div className="flex-1 px-4 pt-2.5 pb-3 cursor-pointer" onClick={onView}>
        {/* Description */}
        {program.description_text ? (
          <p className="text-[11px] text-student-text/80 leading-relaxed line-clamp-3 mb-3">
            {program.description_text}
          </p>
        ) : (
          <div className="flex items-center gap-1.5 text-[11px] text-student-text/50 mb-3">
            <FileText size={11} />
            <span>Program details available on full page</span>
          </div>
        )}

        {/* Stats grid */}
        <div className="grid grid-cols-2 gap-1.5">
          {program.tuition != null && (
            <div className="flex items-center gap-1.5 px-2 py-1.5 rounded-lg bg-slate-50">
              <DollarSign size={11} className="text-student-text/50 flex-shrink-0" />
              <div>
                <p className="text-[10px] text-student-text/60 leading-none">Tuition</p>
                <p className="text-xs font-semibold text-student-ink leading-tight">{formatCurrency(program.tuition)}</p>
              </div>
            </div>
          )}
          {program.median_salary != null && (
            <div className="flex items-center gap-1.5 px-2 py-1.5 rounded-lg bg-slate-50">
              <TrendingUp size={11} className="text-student-text/50 flex-shrink-0" />
              <div>
                <p className="text-[10px] text-student-text/60 leading-none">Avg Salary</p>
                <p className="text-xs font-semibold text-student-ink leading-tight">{formatCurrency(program.median_salary)}</p>
              </div>
            </div>
          )}
          {acceptPct != null && (
            <div className="flex items-center gap-1.5 px-2 py-1.5 rounded-lg bg-slate-50">
              <Percent size={11} className="text-student-text/50 flex-shrink-0" />
              <div>
                <p className="text-[10px] text-student-text/60 leading-none">Acceptance</p>
                <p className="text-xs font-semibold text-student-ink leading-tight">{acceptPct}%</p>
              </div>
            </div>
          )}
          {gradPct != null && (
            <div className="flex items-center gap-1.5 px-2 py-1.5 rounded-lg bg-slate-50">
              <GraduationCap size={11} className="text-student-text/50 flex-shrink-0" />
              <div>
                <p className="text-[10px] text-student-text/60 leading-none">Grad Rate</p>
                <p className="text-xs font-semibold text-student-ink leading-tight">{gradPct}%</p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* ── Actions ── */}
      <div className="flex items-center border-t border-divider mt-auto divide-x divide-divider">
        {onCompare && (
          <button
            onClick={e => { e.stopPropagation(); onCompare() }}
            className={`flex-1 flex items-center justify-center gap-1.5 py-2.5 text-[11px] font-medium transition-colors ${
              comparing ? 'text-student bg-student-mist' : 'text-student-text hover:bg-student-mist hover:text-student-ink'
            }`}
          >
            <ArrowRightLeft size={12} />
            Compare
          </button>
        )}
        {onAskCounselor && (
          <button
            onClick={e => { e.stopPropagation(); onAskCounselor() }}
            className="flex-1 flex items-center justify-center gap-1.5 py-2.5 text-[11px] font-medium text-gold hover:bg-gold-soft transition-colors"
          >
            <MessageSquare size={12} />
            Ask AI
          </button>
        )}
      </div>
    </div>
  )
}
