import type { ReactNode } from 'react'
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

/** Extract credit count from highlights. Returns null if unknown — we don't
 * fall back to a generic default because that would make all programs look
 * the same. */
function creditsForProgram(highlights?: string[] | null): string | null {
  if (!highlights) return null
  for (const h of highlights) {
    const m = h.match(/(\d{2,3})[-\s]?credits?/i)
    if (m) return `${m[1]} credits`
  }
  return null
}

/** Normalize the tracks field — it arrives in several shapes across programs:
 *  - array of strings (Anthropology: ["cultural", "archaeology", ...])
 *  - dict with a named array inside (Accounting: {concentrations: [...], note: ...})
 *  - null / undefined
 * Returns a flat array of track names. */
function tracksArray(tracks: any): string[] {
  if (!tracks) return []
  if (Array.isArray(tracks)) return tracks.filter(t => typeof t === 'string')
  if (typeof tracks === 'object') {
    for (const key of ['concentrations', 'tracks', 'subfields', 'specializations', 'streams', 'pathways']) {
      if (Array.isArray(tracks[key])) {
        return tracks[key].filter((t: any) => typeof t === 'string')
      }
    }
  }
  return []
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
  default: 'bg-card text-foreground border-border/60',
  primary: 'bg-secondary/10 text-secondary border-secondary/20',
  urgent: 'bg-warning-soft text-warning border-warning/40',
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
  /** Spec 11 §6 — archived program: actions are disabled. */
  archived?: boolean
  onBack: () => void
  onSave: () => void
  onCompare?: () => void
  onAskCounselor?: () => void
  onApply?: () => void
  onViewApplication?: () => void
  /** Spec 11 §2 — DualRing (the sole accent) sits inline in the fact strip. */
  matchSlot?: ReactNode
}

export default function ProgramHeader({
  programName, degreeType, institutionId, institutionName, institutionCity,
  institutionCountry, department,
  durationMonths, deliveryFormat, highlights, tracks, description,
  isSaved, isComparing, hasApplication, archived,
  onBack, onSave, onCompare, onAskCounselor, onApply, onViewApplication,
  matchSlot,
}: Props) {
  const degreeLabel = DEGREE_LABELS[degreeType] || degreeType
  const duration = durationLabel(durationMonths, degreeType)
  const format = formatFormat(deliveryFormat)
  const credits = creditsForProgram(highlights)
  const calendar = academicCalendar(highlights)
  const features = extractAcademicFeatures(highlights, description, degreeType)
  const studyMode = degreeType === 'certificate' ? 'Part-time option' : 'Full-time'
  const trackNames = tracksArray(tracks)

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
  if (trackNames.length > 0) {
    pills.push({ icon: Layers, heading: 'Tracks', value: `${trackNames.length}`, title: trackNames.slice(0, 3).join(', ') })
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
    <div className="relative bg-card rounded-lg border border-border overflow-hidden mb-5">
      {/* Top bar: back + secondary actions */}
      <div className="flex items-center justify-between px-5 pt-4">
        <button
          onClick={onBack}
          className="flex items-center gap-1.5 text-xs font-medium text-foreground hover:text-foreground transition-colors"
        >
          <ArrowLeft size={14} />
          Back
        </button>
        <div className="flex items-center gap-1.5">
          <button
            onClick={onSave}
            disabled={archived}
            className={`flex items-center gap-1.5 px-2.5 py-1.5 text-xs font-medium rounded-lg border transition-colors disabled:opacity-50 disabled:cursor-not-allowed ${
              isSaved
                ? 'bg-secondary text-secondary-foreground border-secondary'
                : 'bg-card text-muted-foreground border-border hover:border-secondary hover:text-secondary'
            }`}
            aria-label={isSaved ? 'Saved' : 'Save'}
          >
            {isSaved ? <BookmarkCheck size={12} /> : <Bookmark size={12} />}
            {isSaved ? 'Saved' : 'Save'}
          </button>
          {onCompare && (
            <button
              onClick={onCompare}
              disabled={archived}
              className={`flex items-center gap-1.5 px-2.5 py-1.5 text-xs font-medium rounded-lg border transition-colors disabled:opacity-50 disabled:cursor-not-allowed ${
                isComparing
                  ? 'bg-secondary text-secondary-foreground border-secondary'
                  : 'bg-card text-muted-foreground border-border hover:border-secondary hover:text-secondary'
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
            <h1 className="text-[28px] font-bold text-foreground leading-tight tracking-tight">{programName}</h1>

            {/* Breadcrumb */}
            <div className="flex items-center gap-1 mt-1.5 text-[13px] text-foreground flex-wrap">
              <Link to={`/s/institutions/${institutionId}`} className="text-secondary hover:underline font-medium">
                {institutionName}
              </Link>
              {department && (
                <>
                  <ChevronRight size={11} className="text-foreground/40" />
                  <span>{department}</span>
                </>
              )}
              {(institutionCity || institutionCountry) && (
                <>
                  <span className="text-foreground/40">·</span>
                  <span>{institutionCity ? `${institutionCity}, ` : ''}{institutionCountry}</span>
                </>
              )}
            </div>

            {/* Fact strip — DualRing (the sole accent, §2) leads the standard
                basics: two-line info cards consistent across all programs. */}
            <div className="flex flex-wrap items-center gap-x-4 gap-y-2 mt-4">
              {matchSlot && (
                <div className="flex-shrink-0 pr-4 mr-1 border-r border-border">
                  {matchSlot}
                </div>
              )}
              <div className="flex flex-wrap items-stretch gap-1.5">
                {pills.map((p, i) => (
                  <div
                    key={i}
                    title={p.title}
                    className={`flex items-center gap-2 px-2.5 py-1.5 rounded-lg border ${PILL_TONE[p.tone || 'default']}`}
                  >
                    <p.icon
                      size={14}
                      className={
                        p.tone === 'primary' ? 'text-secondary' :
                        p.tone === 'urgent' ? 'text-warning' :
                        'text-muted-foreground/60'
                      }
                    />
                    <div className="leading-tight">
                      <p className={`text-[9px] uppercase tracking-wider font-semibold ${
                        p.tone === 'primary' ? 'text-secondary/70' :
                        p.tone === 'urgent' ? 'text-warning/80' :
                        'text-muted-foreground/60'
                      }`}>
                        {p.heading}
                      </p>
                      <p className={`text-[13px] font-semibold ${
                        p.tone === 'primary' ? 'text-secondary' :
                        p.tone === 'urgent' ? 'text-warning' :
                        'text-foreground'
                      }`}>
                        {p.value}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Right: Ask Counselor + primary action */}
          <div className="flex-shrink-0 flex flex-col items-stretch gap-2">
            {onAskCounselor && (
              <button
                onClick={onAskCounselor}
                className="flex items-center justify-center gap-1.5 px-3.5 py-2 text-xs font-semibold rounded-lg bg-secondary/5 text-secondary border border-secondary/30 hover:bg-secondary/10 transition-colors"
              >
                <Sparkles size={12} />
                Ask counselor
              </button>
            )}
            {hasApplication && onViewApplication ? (
              <button
                onClick={onViewApplication}
                className="flex items-center gap-1.5 px-3.5 py-2 text-xs font-semibold rounded-lg bg-secondary text-secondary-foreground hover:brightness-95 transition-colors shadow-sm"
              >
                <FileText size={12} /> My application
              </button>
            ) : onApply ? (
              <button
                onClick={onApply}
                disabled={archived}
                className="flex items-center gap-1.5 px-3.5 py-2 text-xs font-semibold rounded-lg bg-secondary text-secondary-foreground hover:brightness-95 transition-colors shadow-sm disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:bg-secondary"
              >
                <Send size={12} /> Start application
              </button>
            ) : null}
          </div>
        </div>
      </div>
    </div>
  )
}
