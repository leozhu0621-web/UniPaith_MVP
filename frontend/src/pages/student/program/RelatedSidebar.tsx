import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Sparkles, ChevronRight, ChevronLeft, Compass } from 'lucide-react'
import Card from '../../../components/ui/Card'
import { DEGREE_LABELS } from '../../../utils/constants'

interface ProgramLink {
  id: string
  program_name: string
  department?: string | null
  degree_type?: string
}

interface Props {
  sameSchoolPrograms?: ProgramLink[]
  similarPrograms?: ProgramLink[]
  /** Campus photo revealed as a gradient backdrop on hover of a fit card. */
  bgPhoto?: string | null
  /** Spec 11 §4 — back to Discovery with this program's attributes pre-applied. */
  discoveryBackHref?: string
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

  return (
    <aside className="space-y-4">

      {/* Programs that fit you — one card at a time, paged with arrows. */}
      {fitPrograms.length > 0 && current && (
        <Card className="p-4">
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
                className="absolute inset-0 bg-cover bg-center opacity-0 group-hover:opacity-30 transition-opacity duration-300"
                style={{ backgroundImage: `url(${bgPhoto})` }}
              />
            )}
            <div className="relative p-4 min-h-[96px] flex flex-col justify-end">
              {current.degree_type && (
                <p className="text-[10px] uppercase tracking-wider font-semibold text-secondary mb-0.5">
                  {DEGREE_LABELS[current.degree_type] || current.degree_type}
                </p>
              )}
              <p className="text-sm font-semibold text-foreground leading-snug group-hover:text-secondary">{current.program_name}</p>
              {current.department && (
                <p className="text-[11px] text-muted-foreground mt-0.5 truncate">{current.department}</p>
              )}
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
