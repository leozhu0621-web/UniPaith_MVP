import { Fragment, useState } from 'react'
import { Link } from 'react-router-dom'
import { Sparkles, ChevronRight, ChevronLeft, Compass } from 'lucide-react'
import Card from '../../../components/ui/Card'
import { DEGREE_LABELS } from '../../../utils/constants'
import { formatCurrency } from '../../../utils/format'

interface ProgramLink {
  id: string
  program_name: string
  department?: string | null
  degree_type?: string
  institution_name?: string | null
  duration_months?: number | null
  delivery_format?: string | null
  tuition?: number | null
  median_salary?: number | null
}

interface Props {
  sameSchoolPrograms?: ProgramLink[]
  similarPrograms?: ProgramLink[]
  /** Campus photo revealed as a gradient backdrop on hover of a fit card. */
  bgPhoto?: string | null
  /** Spec 11 §4 — back to Discovery with this program's attributes pre-applied. */
  discoveryBackHref?: string
}

const FORMAT_LABELS: Record<string, string> = {
  on_campus: 'On-campus',
  in_person: 'On-campus',
  online: 'Online',
  hybrid: 'Hybrid',
}

function prettyFormat(f: string): string {
  return FORMAT_LABELS[f] || f.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
}

function fmtDuration(m?: number | null): string | null {
  if (!m || m <= 0) return null
  if (m % 12 === 0) {
    const y = m / 12
    return `${y} yr${y > 1 ? 's' : ''}`
  }
  return `${m} mo`
}

export default function RelatedSidebar({
  sameSchoolPrograms = [],
  similarPrograms = [],
  bgPhoto,
  discoveryBackHref,
}: Props) {
  // "Programs that fit you" — semantically-recommended programs first; fall back
  // to other programs at the same school so the rail is never empty.
  const fitById = new Map<string, ProgramLink>()
  for (const p of [...similarPrograms, ...sameSchoolPrograms]) {
    if (!fitById.has(p.id)) fitById.set(p.id, p)
  }
  const fitPrograms = [...fitById.values()].slice(0, 6)

  const [idx, setIdx] = useState(0)
  const safeIdx = Math.min(idx, Math.max(0, fitPrograms.length - 1))
  const current = fitPrograms[safeIdx]

  const meta: string[] = []
  if (current) {
    const dur = fmtDuration(current.duration_months)
    if (dur) meta.push(dur)
    if (current.delivery_format) meta.push(prettyFormat(current.delivery_format))
    if (current.tuition) meta.push(`${formatCurrency(current.tuition)}/yr`)
    else if (current.median_salary) meta.push(`${formatCurrency(current.median_salary)} median`)
  }
  const subtitle = current?.department || current?.institution_name || null

  return (
    <aside className="space-y-4">

      {/* Programs that fit you — one richer card at a time, paged with arrows. */}
      {fitPrograms.length > 0 && current && (
        <Card pad={false} className="p-4">
          <div className="flex items-center gap-2 mb-3">
            <Sparkles size={14} className="text-secondary" />
            <h3 className="text-sm font-semibold text-foreground">Programs that fit you</h3>
          </div>

          <Link
            to={`/s/programs/${current.id}`}
            className="group relative block rounded-xl border border-border overflow-hidden hover:border-secondary/40 hover:shadow-sm transition-all"
          >
            <div className="absolute inset-0 bg-gradient-to-br from-secondary/15 to-muted" />
            {bgPhoto && (
              <div
                className="absolute inset-0 bg-cover bg-center opacity-0 group-hover:opacity-25 transition-opacity duration-300"
                style={{ backgroundImage: `url(${bgPhoto})` }}
              />
            )}
            <div className="relative p-5 min-h-[156px] flex flex-col justify-end">
              {current.degree_type && (
                <p className="text-[10px] uppercase tracking-wider font-semibold text-secondary mb-1">
                  {DEGREE_LABELS[current.degree_type] || current.degree_type}
                </p>
              )}
              <p className="text-base font-bold text-foreground leading-snug group-hover:text-secondary line-clamp-2">{current.program_name}</p>
              {subtitle && (
                <p className="text-[11px] text-muted-foreground mt-1 truncate">{subtitle}</p>
              )}
              {meta.length > 0 && (
                <div className="flex flex-wrap items-center gap-x-2 gap-y-1 mt-2.5 text-[11px] text-foreground/70">
                  {meta.map((m, i) => (
                    <Fragment key={i}>
                      {i > 0 && <span className="text-border" aria-hidden="true">·</span>}
                      <span>{m}</span>
                    </Fragment>
                  ))}
                </div>
              )}
              <span className="mt-3 inline-flex items-center gap-1 text-[11px] font-semibold text-secondary opacity-0 group-hover:opacity-100 transition-opacity">
                View program <ChevronRight size={12} />
              </span>
            </div>
          </Link>

          {fitPrograms.length > 1 && (
            <div className="flex items-center justify-between mt-3">
              <button
                type="button"
                onClick={() => setIdx((safeIdx - 1 + fitPrograms.length) % fitPrograms.length)}
                aria-label="Previous program"
                className="w-7 h-7 rounded-full border border-border flex items-center justify-center text-foreground/60 hover:text-secondary hover:border-secondary/40 transition-colors"
              >
                <ChevronLeft size={15} />
              </button>
              <span className="text-[11px] text-muted-foreground tabular-nums">{safeIdx + 1} / {fitPrograms.length}</span>
              <button
                type="button"
                onClick={() => setIdx((safeIdx + 1) % fitPrograms.length)}
                aria-label="Next program"
                className="w-7 h-7 rounded-full border border-border flex items-center justify-center text-foreground/60 hover:text-secondary hover:border-secondary/40 transition-colors"
              >
                <ChevronRight size={15} />
              </button>
            </div>
          )}
        </Card>
      )}

      {/* Back to Discovery with these attributes pre-applied (§4) */}
      {discoveryBackHref && (
        <Link
          to={discoveryBackHref}
          className="flex items-center justify-between gap-2 px-3 py-3 rounded-lg border border-border hover:border-secondary hover:bg-muted transition-colors group"
        >
          <div className="flex items-center gap-2 min-w-0">
            <Compass size={14} className="text-secondary flex-shrink-0" />
            <span className="text-xs font-medium text-foreground">
              Find more like this in Discovery
            </span>
          </div>
          <ChevronRight size={12} className="text-foreground/40 group-hover:text-secondary flex-shrink-0" />
        </Link>
      )}
    </aside>
  )
}
