import { Link } from 'react-router-dom'
import {
  ArrowLeft, Bookmark, BookmarkCheck, ArrowRightLeft, Sparkles,
  Send, ChevronRight, GraduationCap, Clock, Building2, Calendar, FileText,
  BookOpen, Globe, FileCheck, CreditCard, Award, CalendarDays, ClipboardList,
} from 'lucide-react'
import MatchRing from './MatchRing'
import { DEGREE_LABELS } from '../../../utils/constants'
import { formatDate } from '../../../utils/format'
import { differenceInDays } from 'date-fns'

/* ── Helpers ─────────────────────────────────────────────────────────── */

function durationLabel(months?: number | null, degreeType?: string): string | null {
  if (months) {
    if (months >= 12) {
      const y = Math.round(months / 12)
      return `${y} year${y > 1 ? 's' : ''}`
    }
    return `${months} mo`
  }
  if (degreeType === 'bachelors') return '4 years'
  if (degreeType === 'masters') return '2 years'
  if (degreeType === 'phd') return '5 years'
  if (degreeType === 'certificate') return '1 year'
  return null
}

function formatFormat(f?: string | null): string | null {
  if (!f) return 'On Campus'
  const map: Record<string, string> = {
    on_campus: 'On Campus', online: 'Online',
    hybrid: 'Hybrid', in_person: 'In-Person',
  }
  return map[f] || f.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
}

function creditsForDegree(degreeType: string, highlights?: string[] | null): string | null {
  // Try to extract from highlights first (e.g. "128-credit liberal arts curriculum")
  if (highlights) {
    for (const h of highlights) {
      const m = h.match(/(\d{2,3})[-\s]?credit/i)
      if (m) return `${m[1]} credits`
    }
  }
  // Sensible defaults so every program has this pill
  if (degreeType === 'bachelors') return '120 credits'
  if (degreeType === 'masters') return '30 credits'
  if (degreeType === 'phd') return '60+ credits'
  if (degreeType === 'certificate') return '12 credits'
  return null
}

/** Extract application-related basics from the structured requirements list. */
function extractAppInfo(appReqs?: any[] | null) {
  const info: {
    platform?: string
    testPolicy?: string
    appFee?: string
    essaysCount?: number
    recsCount?: number
  } = {}
  if (!Array.isArray(appReqs)) return info

  for (const r of appReqs) {
    const label = String(r.label || '').toLowerCase()
    const note = String(r.note || '')
    if (!info.platform && /common application\b/.test(label) && !label.includes('essay')) {
      info.platform = 'Common App'
    }
    if (!info.platform && /coalition/.test(label)) {
      info.platform = 'Coalition'
    }
    if (/application fee/.test(label) && note) {
      const m = note.match(/\$?(\d+)/)
      if (m) info.appFee = `$${m[1]} fee`
    }
    if (/\bsat\b|\bact\b/.test(label)) {
      if (r.required === false) info.testPolicy = 'Test-flexible'
      else if (r.required === true) info.testPolicy = 'Test-required'
    }
    if (/essay/.test(label)) {
      // Count essay items (e.g., "Common App Essay", "NYU-Specific Essays")
      info.essaysCount = (info.essaysCount || 0) + 1
    }
    if (/recommend/.test(label)) {
      info.recsCount = (info.recsCount || 0) + 1
    }
  }

  // Derive test policy default if nothing specific
  if (!info.testPolicy) info.testPolicy = 'Test-optional'

  return info
}

function startTermLabel(programStartDate?: string | null): string | null {
  if (!programStartDate) return null
  const d = new Date(programStartDate)
  if (isNaN(d.getTime())) return null
  const m = d.getMonth()
  const y = d.getFullYear()
  if (m >= 6 && m <= 8) return `Starts Fall ${y}`
  if (m >= 0 && m <= 1) return `Starts Spring ${y}`
  if (m >= 2 && m <= 5) return `Starts Spring ${y}`
  if (m >= 9 && m <= 11) return `Starts Winter ${y}`
  return `Starts ${d.toLocaleDateString('en-US', { month: 'short', year: 'numeric' })}`
}

/** A pill row item. */
interface Pill {
  icon: any
  label: string
  tone?: 'default' | 'primary' | 'urgent'
  title?: string
}

const PILL_TONE = {
  default: 'bg-slate-50 text-student-ink border-slate-200',
  primary: 'bg-student-mist text-student border-student/15 font-semibold',
  urgent: 'bg-amber-50 text-amber-700 border-amber-200 font-semibold',
}

/* ── Component ───────────────────────────────────────────────────────── */

interface Props {
  programName: string
  degreeType: string
  institutionId: string
  institutionName: string
  institutionCity?: string | null
  institutionCountry?: string | null
  department?: string | null

  // Standard program basics
  durationMonths?: number | null
  deliveryFormat?: string | null
  applicationDeadline?: string | null
  programStartDate?: string | null
  applicationRequirements?: any[] | null
  highlights?: string[] | null
  tracks?: string[] | null

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
  institutionCountry, department,
  durationMonths, deliveryFormat, applicationDeadline, programStartDate,
  applicationRequirements, highlights, tracks,
  matchScore, matchTier, onMatchClick,
  isSaved, isComparing, hasApplication,
  onBack, onSave, onCompare, onAskCounselor, onApply, onViewApplication,
}: Props) {
  const degreeLabel = DEGREE_LABELS[degreeType] || degreeType
  const duration = durationLabel(durationMonths, degreeType)
  const format = formatFormat(deliveryFormat)
  const credits = creditsForDegree(degreeType, highlights)
  const startTerm = startTermLabel(programStartDate)
  const appInfo = extractAppInfo(applicationRequirements)
  const deadline = applicationDeadline
    ? {
        date: formatDate(applicationDeadline),
        days: differenceInDays(new Date(applicationDeadline), new Date()),
      }
    : null
  const deadlineUrgent = deadline && deadline.days >= 0 && deadline.days <= 30

  // Build the standard pill set — same shape for every program.
  const pills: Pill[] = []
  // 1. Degree (primary identifier)
  pills.push({ icon: GraduationCap, label: degreeLabel, tone: 'primary', title: 'Degree awarded' })
  // 2. Duration
  if (duration) pills.push({ icon: Clock, label: duration, title: 'Typical length' })
  // 3. Delivery format
  if (format) pills.push({ icon: Building2, label: format, title: 'How classes are delivered' })
  // 4. Credits
  if (credits) pills.push({ icon: BookOpen, label: credits, title: 'Credits to graduate' })
  // 5. Language of instruction (default English for US programs)
  pills.push({ icon: Globe, label: 'English', title: 'Language of instruction' })
  // 6. Start term
  if (startTerm) pills.push({ icon: CalendarDays, label: startTerm, title: 'When classes begin' })
  // 7. Application platform (if known)
  if (appInfo.platform) pills.push({ icon: ClipboardList, label: appInfo.platform, title: 'How to apply' })
  // 8. Test policy
  if (appInfo.testPolicy) pills.push({ icon: FileCheck, label: appInfo.testPolicy, title: 'SAT / ACT policy' })
  // 9. Application fee
  if (appInfo.appFee) pills.push({ icon: CreditCard, label: appInfo.appFee, title: 'Application fee' })
  // 10. Specializations count (if any)
  if (tracks && tracks.length > 0) {
    pills.push({ icon: Award, label: `${tracks.length} tracks`, title: tracks.slice(0, 3).join(', ') })
  }
  // Deadline as the last pill (urgent styling if close)
  if (deadline && deadline.days >= 0) {
    pills.push({
      icon: Calendar,
      label: deadlineUrgent ? `Apply by ${deadline.date} · ${deadline.days}d left` : `Apply by ${deadline.date}`,
      tone: deadlineUrgent ? 'urgent' : 'default',
      title: 'Application deadline',
    })
  }

  return (
    <div className="relative bg-white rounded-2xl border border-divider overflow-hidden mb-5">
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
          {/* Title block */}
          <div className="flex-1 min-w-0">
            <h1 className="text-[28px] font-bold text-student-ink leading-tight tracking-tight">{programName}</h1>

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

            {/* Standard basics — ~7–10 pills consistent across all programs */}
            <div className="flex flex-wrap items-center gap-1.5 mt-4">
              {pills.map((p, i) => (
                <span
                  key={i}
                  title={p.title}
                  className={`inline-flex items-center gap-1.5 px-2.5 py-1 text-[11px] rounded-md border whitespace-nowrap ${PILL_TONE[p.tone || 'default']}`}
                >
                  <p.icon size={11} className={p.tone === 'primary' ? 'text-student' : p.tone === 'urgent' ? 'text-amber-500' : 'text-slate-400'} />
                  {p.label}
                </span>
              ))}
            </div>
          </div>

          {/* Right: match ring + primary action */}
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
                <FileText size={12} /> My Application
              </button>
            ) : onApply ? (
              <button
                onClick={onApply}
                className="flex items-center gap-1.5 px-3.5 py-2 text-xs font-semibold rounded-lg bg-student text-white hover:bg-student-hover transition-colors shadow-sm"
              >
                <Send size={12} /> Apply Now
              </button>
            ) : null}
          </div>
        </div>
      </div>
    </div>
  )
}
