import { Link } from 'react-router-dom'
import {
  ArrowLeft, Bookmark, BookmarkCheck, ArrowRightLeft, Sparkles,
  Send, Award, ChevronRight, GraduationCap, Clock, Building2,
  MapPin, Users as UsersIcon, Calendar,
} from 'lucide-react'
import MatchRing from './MatchRing'
import { DEGREE_LABELS } from '../../../utils/constants'
import { formatDate } from '../../../utils/format'
import { differenceInDays } from 'date-fns'

/**
 * Visual identity per degree — subtle color accent so the page still feels
 * branded without a large hero image. Color shows up only as left edge,
 * monogram tile background, and a thin top stripe.
 */
const DEGREE_THEME: Record<string, { monoBg: string; monoText: string; stripe: string; accent: string }> = {
  bachelors:   { monoBg: 'bg-indigo-50',  monoText: 'text-indigo-700',  stripe: 'bg-gradient-to-r from-blue-500 via-indigo-500 to-indigo-600',   accent: 'border-l-indigo-500'  },
  masters:     { monoBg: 'bg-purple-50',  monoText: 'text-purple-700',  stripe: 'bg-gradient-to-r from-violet-500 via-purple-500 to-fuchsia-500', accent: 'border-l-purple-500'  },
  phd:         { monoBg: 'bg-slate-100',  monoText: 'text-slate-800',   stripe: 'bg-gradient-to-r from-slate-700 via-slate-800 to-zinc-900',     accent: 'border-l-slate-700'   },
  certificate: { monoBg: 'bg-emerald-50', monoText: 'text-emerald-700', stripe: 'bg-gradient-to-r from-emerald-500 via-teal-500 to-cyan-500',    accent: 'border-l-emerald-500' },
  doctorate:   { monoBg: 'bg-rose-50',    monoText: 'text-rose-700',    stripe: 'bg-gradient-to-r from-rose-500 via-pink-500 to-rose-600',       accent: 'border-l-rose-500'    },
}

function degreeAbbrev(degree: string): string {
  const map: Record<string, string> = {
    bachelors: 'BS', masters: 'MS', phd: 'PhD',
    certificate: 'CERT', doctorate: 'DOC', associate: 'AA',
  }
  return map[degree] || degree.slice(0, 3).toUpperCase()
}

function durationLabel(months?: number | null, degreeType?: string): string | null {
  if (months) {
    if (months >= 12) {
      const y = Math.round(months / 12)
      return `${y} year${y > 1 ? 's' : ''}`
    }
    return `${months} mo`
  }
  if (degreeType === 'bachelors') return '4 years'
  if (degreeType === 'masters') return '1–2 years'
  if (degreeType === 'phd') return '4–6 years'
  return null
}

function formatFormat(f?: string | null): string | null {
  if (!f) return null
  const map: Record<string, string> = {
    on_campus: 'On Campus', online: 'Online',
    hybrid: 'Hybrid', in_person: 'In-Person',
  }
  return map[f] || f.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
}

interface Props {
  programName: string
  degreeType: string
  institutionId: string
  institutionName: string
  institutionCity?: string | null
  institutionCountry?: string | null
  institutionLogoUrl?: string | null
  department?: string | null
  usNewsRank?: number | null

  // Info pills
  durationMonths?: number | null
  deliveryFormat?: string | null
  campusSetting?: string | null
  studentBodySize?: number | null
  applicationDeadline?: string | null

  // Match
  matchScore?: number | null
  matchTier?: number | null
  onMatchClick?: () => void

  // Actions
  isSaved: boolean
  isComparing?: boolean
  hasApplication?: boolean
  onBack: () => void
  onSave: () => void
  onCompare?: () => void
  onAskCounselor?: () => void
  onApply?: () => void
  onViewApplication?: () => void
}

export default function ProgramHeader({
  programName, degreeType, institutionId, institutionName, institutionCity,
  institutionCountry, institutionLogoUrl, department, usNewsRank,
  durationMonths, deliveryFormat, campusSetting, studentBodySize, applicationDeadline,
  matchScore, matchTier, onMatchClick,
  isSaved, isComparing, hasApplication,
  onBack, onSave, onCompare, onAskCounselor, onApply, onViewApplication,
}: Props) {
  const theme = DEGREE_THEME[degreeType] || DEGREE_THEME.bachelors
  const abbrev = degreeAbbrev(degreeType)
  const degreeLabel = DEGREE_LABELS[degreeType] || degreeType
  const duration = durationLabel(durationMonths, degreeType)
  const format = formatFormat(deliveryFormat)
  const deadline = applicationDeadline
    ? {
        date: formatDate(applicationDeadline),
        days: differenceInDays(new Date(applicationDeadline), new Date()),
      }
    : null
  const deadlineUrgent = deadline && deadline.days >= 0 && deadline.days <= 30

  return (
    <div className={`relative bg-white rounded-2xl border border-divider overflow-hidden mb-5 border-l-4 ${theme.accent}`}>
      {/* Thin color stripe on top */}
      <div className={`h-1 w-full ${theme.stripe}`} />

      {/* Top bar: back + secondary actions */}
      <div className="flex items-center justify-between px-5 pt-4">
        <button
          onClick={onBack}
          className="flex items-center gap-1.5 text-xs font-medium text-student-text hover:text-student-ink transition-colors"
        >
          <ArrowLeft size={14} />
          Back
        </button>
        <div className="flex items-center gap-1.5">
          <button
            onClick={onSave}
            className={`flex items-center gap-1.5 px-2.5 py-1.5 text-xs font-medium rounded-lg border transition-colors ${
              isSaved
                ? 'bg-student text-white border-student'
                : 'bg-white text-student-text border-divider hover:border-student hover:text-student'
            }`}
            aria-label={isSaved ? 'Saved' : 'Save'}
          >
            {isSaved ? <BookmarkCheck size={12} /> : <Bookmark size={12} />}
            {isSaved ? 'Saved' : 'Save'}
          </button>
          {onCompare && (
            <button
              onClick={onCompare}
              className={`flex items-center gap-1.5 px-2.5 py-1.5 text-xs font-medium rounded-lg border transition-colors ${
                isComparing
                  ? 'bg-student text-white border-student'
                  : 'bg-white text-student-text border-divider hover:border-student hover:text-student'
              }`}
            >
              <ArrowRightLeft size={12} />
              Compare
            </button>
          )}
          {onAskCounselor && (
            <button
              onClick={onAskCounselor}
              className="flex items-center gap-1.5 px-2.5 py-1.5 text-xs font-medium rounded-lg bg-gold-soft text-gold border border-gold/20 hover:bg-gold hover:text-white transition-colors"
            >
              <Sparkles size={12} />
              Ask AI
            </button>
          )}
        </div>
      </div>

      {/* Main content */}
      <div className="px-5 pt-3 pb-4">
        <div className="flex items-start gap-4">
          {/* Degree monogram + logo stack */}
          <div className="flex-shrink-0 flex flex-col items-center gap-2">
            <div className={`w-16 h-16 rounded-xl ${theme.monoBg} border border-divider flex flex-col items-center justify-center shadow-sm`}>
              <GraduationCap size={16} className={theme.monoText} />
              <span className={`text-xs font-black tracking-wide ${theme.monoText} leading-none mt-0.5`}>
                {abbrev}
              </span>
            </div>
            {institutionLogoUrl && (
              <img
                src={institutionLogoUrl}
                alt=""
                className="w-8 h-8 rounded-md object-contain bg-white border border-divider p-0.5"
                onError={e => (e.currentTarget.style.display = 'none')}
              />
            )}
          </div>

          {/* Title block */}
          <div className="flex-1 min-w-0">
            <h1 className="text-[26px] font-bold text-student-ink leading-tight">{programName}</h1>

            {/* Breadcrumb */}
            <div className="flex items-center gap-1 mt-1.5 text-[13px] text-student-text flex-wrap">
              <Link to={`/s/institutions/${institutionId}`} className="text-student hover:underline font-medium">
                {institutionName}
              </Link>
              {department && (
                <>
                  <ChevronRight size={11} className="text-student-text/40" />
                  <span>{department}</span>
                </>
              )}
              {(institutionCity || institutionCountry) && (
                <>
                  <span className="text-student-text/40">·</span>
                  <span>{institutionCity ? `${institutionCity}, ` : ''}{institutionCountry}</span>
                </>
              )}
            </div>

            {/* Badges row */}
            <div className="flex flex-wrap items-center gap-1.5 mt-3">
              <span className={`inline-flex items-center gap-1 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider rounded-md ${theme.monoBg} ${theme.monoText} border border-divider`}>
                <GraduationCap size={10} />
                {degreeLabel}
              </span>
              {usNewsRank && (
                <span
                  className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-gold-soft text-gold border border-gold/20"
                  title="US News National University Ranking 2025"
                >
                  <Award size={10} />
                  <span className="text-[10px] font-bold">#{usNewsRank} US News 2025</span>
                </span>
              )}
            </div>

            {/* Info pills row */}
            <div className="flex flex-wrap items-center gap-1.5 mt-3">
              {duration && (
                <span className="inline-flex items-center gap-1 px-2 py-0.5 text-[11px] rounded-md bg-slate-50 text-student-ink border border-slate-200">
                  <Clock size={11} className="text-slate-400" />
                  {duration}
                </span>
              )}
              {format && (
                <span className="inline-flex items-center gap-1 px-2 py-0.5 text-[11px] rounded-md bg-slate-50 text-student-ink border border-slate-200">
                  <Building2 size={11} className="text-slate-400" />
                  {format}
                </span>
              )}
              {campusSetting && (
                <span className="inline-flex items-center gap-1 px-2 py-0.5 text-[11px] rounded-md bg-slate-50 text-student-ink border border-slate-200 capitalize">
                  <MapPin size={11} className="text-slate-400" />
                  {campusSetting}
                </span>
              )}
              {studentBodySize ? (
                <span className="inline-flex items-center gap-1 px-2 py-0.5 text-[11px] rounded-md bg-slate-50 text-student-ink border border-slate-200">
                  <UsersIcon size={11} className="text-slate-400" />
                  {studentBodySize.toLocaleString()} students
                </span>
              ) : null}
              {deadline && deadline.days >= 0 && (
                <span
                  className={`inline-flex items-center gap-1 px-2 py-0.5 text-[11px] rounded-md border ${
                    deadlineUrgent
                      ? 'bg-amber-50 text-amber-700 border-amber-200 font-semibold'
                      : 'bg-slate-50 text-student-ink border-slate-200'
                  }`}
                >
                  <Calendar size={11} className={deadlineUrgent ? 'text-amber-500' : 'text-slate-400'} />
                  {deadlineUrgent ? `⚡ Deadline in ${deadline.days}d · ${deadline.date}` : `Deadline ${deadline.date}`}
                </span>
              )}
            </div>
          </div>

          {/* Right: match ring + apply */}
          <div className="flex-shrink-0 flex flex-col items-end gap-2.5">
            {matchScore != null && matchTier != null && (
              <button
                onClick={onMatchClick}
                className="hover:opacity-90 transition-opacity"
                title="See match breakdown"
              >
                <MatchRing score={matchScore} tier={matchTier} size={64} />
              </button>
            )}
            {hasApplication && onViewApplication ? (
              <button
                onClick={onViewApplication}
                className="flex items-center gap-1.5 px-3.5 py-2 text-xs font-semibold rounded-lg bg-student text-white hover:bg-student-hover transition-colors shadow-sm"
              >
                View Application
              </button>
            ) : onApply ? (
              <button
                onClick={onApply}
                className="flex items-center gap-1.5 px-3.5 py-2 text-xs font-semibold rounded-lg bg-student text-white hover:bg-student-hover transition-colors shadow-sm"
              >
                <Send size={12} /> Apply
              </button>
            ) : null}
          </div>
        </div>
      </div>
    </div>
  )
}
