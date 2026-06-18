import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { ArrowRight, Sparkles } from 'lucide-react'
import { SectionHeader } from '../../../../components/student/density'
import BandBadge from '../../../../components/ui/BandBadge'
import type { Band } from '../../../../components/ui/BandBadge'
import { getMatches } from '../../../../api/matching'
import type { MatchResultDual } from '../../../../types'

/** Fitness/confidence arrive as strings (Phase A). Normalize to 0..1 the same
 *  way MatchCard does. */
function toUnit(v: string | number | null | undefined): number {
  const n = typeof v === 'string' ? parseFloat(v) : (v ?? 0)
  if (!Number.isFinite(n)) return 0
  const u = n > 1 ? n / 100 : n
  return Math.max(0, Math.min(1, u))
}

/** A compact peek at the student's strongest matches (Spec 2026-06-14 backlog →
 *  promoted). Discovery lives in /s/explore; this is a home teaser that
 *  deep-links there. Hides entirely when there are no matches yet. */
export default function TopMatchesPeek({ className }: { className?: string }) {
  const navigate = useNavigate()
  const { data: matches = [] } = useQuery({
    queryKey: ['matches'],
    queryFn: () => getMatches(),
    retry: 1,
    staleTime: 60_000,
  })

  const top = (matches as MatchResultDual[]).slice(0, 3)
  if (top.length === 0) return null

  return (
    <div className={className}>
      <SectionHeader
        action={
          <button onClick={() => navigate('/s/explore')} className="inline-flex items-center gap-1 text-xs text-secondary hover:underline">
            See all <ArrowRight size={12} />
          </button>
        }
      >
        Your top matches
      </SectionHeader>
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {top.map(m => {
          // AI-Structure-3 §14 — the student response no longer carries a raw
          // fitness number; show the precise % only when a score is present
          // (cached/institution payloads), otherwise the band carries the readout.
          const hasRaw = m.fitness_score != null && m.fitness_score !== ''
          const fitness = Math.round(toUnit(m.fitness_score) * 100)
          return (
            <button
              key={m.program_id}
              onClick={() => navigate(`/s/programs/${m.program_id}`)}
              className="flex flex-col rounded-lg border border-border bg-card p-3 text-left transition-shadow hover:elev-raised"
            >
              <p className="line-clamp-2 text-sm font-semibold text-foreground">{m.program_name ?? 'Program'}</p>
              {m.institution_name && <p className="mt-0.5 truncate text-xs text-muted-foreground">{m.institution_name}</p>}
              <div className="mt-2 flex items-center gap-2">
                {m.band_label && <BandBadge band={m.band_label as Band} />}
                {hasRaw && (
                  <span className="ml-auto inline-flex items-center gap-1 text-xs font-semibold text-secondary">
                    <Sparkles size={12} /> {fitness}% fit
                  </span>
                )}
              </div>
            </button>
          )
        })}
      </div>
    </div>
  )
}
