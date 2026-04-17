import { Link } from 'react-router-dom'
import {
  ArrowLeft, Bookmark, BookmarkCheck, ArrowRightLeft, Sparkles,
  Send, ChevronRight, GraduationCap, Clock, Building2, FileText,
  BookOpen, Globe, Award, Briefcase, FlaskConical, Plane, Layers,
  Users, CalendarDays,
} from 'lucide-react'
import { DEGREE_LABELS } from '../../../utils/constants'

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

/** Inspect highlights + description for academic features that describe the
 * program's character (thesis, research, internships, etc.). */
function extractAcademicFeatures(highlights?: string[] | null, description?: string | null, degreeType?: string) {
  const allText = [...(highlights || []), description || ''].join(' ').toLowerCase()
  return {
    hasThesis: /thesis|capstone|dissertation/.test(allText) || degreeType === 'phd',
    hasHonors: /\bhonors\b/.test(allText),
    hasResearch: /research|laboratory|lab[- ]?based/.test(allText) || degreeType === 'phd',
    hasInternship: /internship|co[- ]?op|field[- ]?work|practicum/.test(allText),
    hasStudyAbroad: /study abroad|international experience|global campus/.test(allText),
  }
}

/** Semester system used by the institution — most US schools are semester; we
 * default to that unless we see a hint otherwise. */
function academicCalendar(highlights?: string[] | null): string {
  const txt = (highlights || []).join(' ').toLowerCase()
  if (/\bquarter\b/.test(txt)) return 'Quarter'
  if (/\btrimester\b/.test(txt)) return 'Trimester'
  return 'Semester'
}

/** A pill row item. */
interface Pill {
  icon: any
  /** Small uppercase label shown on top of the card (e.g., "DEGREE"). */
  heading: string
  /** The actual value shown below (e.g., "B.S."). */
  value: string
  tone?: 'default' | 'primary' | 'urgent'
  title?: string
}

const PILL_TONE = {
  default: 'bg-white text-student-ink border-divider',
  primary: 'bg-student-mist text-student border-student/15',
  urgent: 'bg-amber-50 text-amber-700 border-amber-200',
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

  // Program academic character
  durationMonths?: number | null
  deliveryFormat?: string | null
  highlights?: string[] | null
  tracks?: string[] | null
  description?: string | null

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
  durationMonths, deliveryFormat, highlights, tracks, description,
  isSaved, isComparing, hasApplication,
  onBack, onSave, onCompare, onAskCounselor, onApply, onViewApplication,
}: Props) {
  const degreeLabel = DEGREE_LABELS[degreeType] || degreeType
  const duration = durationLabel(durationMonths, degreeType)
  const format = formatFormat(deliveryFormat)
  const credits = creditsForDegree(degreeType, highlights)
  const calendar = academicCalendar(highlights)
  const features = extractAcademicFeatures(highlights, description, degreeType)
  const studyMode = degreeType === 'certificate' ? 'Part-time option' : 'Full-time'

  // Build ~7–10 two-line info cards describing the program's ACADEMIC CHARACTER.
  // Each card has a small uppercase heading and a value below — self-explanatory
  // without having to hover for a tooltip.
  const pills: Pill[] = []
  pills.push({ icon: GraduationCap, heading: 'Degree',   value: degreeLabel, tone: 'primary' })
  if (duration) pills.push({ icon: Clock,       heading: 'Duration',  value: duration })
  if (format)   pills.push({ icon: Building2,   heading: 'Format',    value: format })
  if (credits)  pills.push({ icon: BookOpen,    heading: 'Credits',   value: credits.replace(/\s*credits?$/i, '') })
  pills.push({ icon: Users,      heading: 'Study mode', value: studyMode })
  pills.push({ icon: CalendarDays, heading: 'Calendar',  value: calendar })
  pills.push({ icon: Globe,      heading: 'Language',  value: 'English' })
  if (tracks && tracks.length > 0) {
    pills.push({ icon: Layers, heading: 'Tracks', value: `${tracks.length}`, title: tracks.slice(0, 3).join(', ') })
  }
  if (features.hasThesis) {
    pills.push({
      icon: FileText,
      heading: degreeType === 'phd' ? 'Dissertation' : 'Thesis',
      value: degreeType === 'phd' ? 'Required' : features.hasHonors ? 'Honors' : 'Offered',
    })
  }
  if (features.hasResearch) {
    pills.push({ icon: FlaskConical, heading: 'Research', value: 'Active' })
  }
  if (features.hasInternship) {
    pills.push({ icon: Briefcase, heading: 'Internships', value: 'Supported' })
  }
  if (features.hasStudyAbroad) {
    pills.push({ icon: Plane, heading: 'Study abroad', value: 'Available' })
  }
  if (features.hasHonors && !pills.some(p => p.value === 'Honors')) {
    pills.push({ icon: Award, heading: 'Honors track', value: 'Available' })
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

            {/* Standard basics — two-line info cards consistent across all programs */}
            <div className="flex flex-wrap items-stretch gap-1.5 mt-4">
              {pills.map((p, i) => (
                <div
                  key={i}
                  title={p.title}
                  className={`flex items-center gap-2 px-2.5 py-1.5 rounded-lg border ${PILL_TONE[p.tone || 'default']}`}
                >
                  <p.icon
                    size={14}
                    className={
                      p.tone === 'primary' ? 'text-student' :
                      p.tone === 'urgent' ? 'text-amber-500' :
                      'text-student-text/50'
                    }
                  />
                  <div className="leading-tight">
                    <p className={`text-[9px] uppercase tracking-wider font-semibold ${
                      p.tone === 'primary' ? 'text-student/70' :
                      p.tone === 'urgent' ? 'text-amber-700/80' :
                      'text-student-text/60'
                    }`}>
                      {p.heading}
                    </p>
                    <p className={`text-[13px] font-semibold ${
                      p.tone === 'primary' ? 'text-student' :
                      p.tone === 'urgent' ? 'text-amber-800' :
                      'text-student-ink'
                    }`}>
                      {p.value}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Right: Ask Counselor CTA + primary action */}
          <div className="flex-shrink-0 flex flex-col items-stretch gap-2.5 w-[220px]">
            {onAskCounselor && (
              <button
                onClick={onAskCounselor}
                className="group text-left rounded-xl border border-gold/20 bg-gradient-to-br from-gold-soft to-amber-50 px-4 py-3 hover:border-gold/40 hover:shadow-sm transition-all"
              >
                <div className="flex items-center gap-2 mb-1">
                  <div className="w-7 h-7 rounded-lg bg-white flex items-center justify-center shadow-sm">
                    <Sparkles size={13} className="text-gold" />
                  </div>
                  <div>
                    <p className="text-[10px] uppercase tracking-wider font-bold text-gold/80">Not sure?</p>
                    <p className="text-[13px] font-bold text-student-ink leading-tight">Ask your counselor</p>
                  </div>
                </div>
                <p className="text-[11px] text-student-text leading-relaxed mt-1.5 group-hover:text-student-ink transition-colors">
                  Get a personalized take on whether {programName} fits your goals.
                </p>
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
