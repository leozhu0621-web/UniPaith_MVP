/**
 * Strategy → "Your school list".
 *
 * The white-paper model: a strategy isn't just an angle, it's a balanced LIST
 * of programs. Each row shows two SEPARATE signals — Fitness (how well the
 * program suits you, `fitness_score`) and Odds (the admission band, `band_label`)
 * — plus the same one-line counselor read Discover shows (`matchStoryline`, #969),
 * so a school reads identically on both surfaces. Keeping fit and odds apart is
 * the point: a reach can still be an excellent fit.
 *
 * Reads the same `getMatches()` (`['matches']`) the Discover hub uses, so the
 * list here always lines up with the full matches view it links to. No bars,
 * no tables — just plain cards with word tags + the storyline. Self-hides to a
 * calm empty line when there are no matches yet.
 */
import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'

import { getMatches } from '../../../../api/matching'
import { matchStoryline } from '../../match/matchStoryline'
import type { MatchResultDual } from '../../../../types'
import { fitWord, oddsWord } from './scoreWords'

const TOP_N = 6

/** Best display name for a match row. */
function matchName(m: MatchResultDual): string {
  const program = m.program_name ?? m.degree_type ?? 'Program'
  return m.institution_name ? `${m.institution_name} — ${program}` : program
}

/** A one-line reason, if the match carries any prose. */
function matchReason(m: MatchResultDual): string | null {
  const reason = m.rationale_text ?? m.reasoning_text
  return reason && reason.trim() ? reason.trim() : null
}

function WordTag({
  label,
  word,
  tone,
}: {
  label: string
  word: string
  tone: 'fit' | 'odds'
}) {
  const toneClass =
    tone === 'fit' ? 'bg-secondary/10 text-secondary' : 'bg-muted text-muted-foreground'
  return (
    <span className={`rounded-full px-2 py-0.5 text-xs ${toneClass}`}>
      <span className="font-medium">{label}</span> {word}
    </span>
  )
}

function SchoolRow({ match }: { match: MatchResultDual }) {
  // Prefer the server's simple range-based fit_label; fall back to the legacy
  // fitness_score word for institution/cached payloads that still carry it.
  const fit = match.fit_label ?? fitWord(match.fitness_score)
  const odds = oddsWord(match.band_label)
  // The same plain-language counselor read Discover shows (#969). It encodes fit
  // vs odds in prose; fall back to any stored rationale when no band is served.
  const fitness = Number(match.fitness_score)
  const hasFitness = match.fitness_score != null && Number.isFinite(fitness) && fitness > 0
  const reason = matchStoryline(match.band_label, hasFitness ? fitness : 0, hasFitness) || matchReason(match)

  return (
    <div className="rounded-md border border-border bg-card p-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="min-w-0 text-sm font-medium text-foreground">{matchName(match)}</div>
        {(fit || odds) && (
          <div className="flex shrink-0 items-center gap-1.5">
            {fit && (
              <span className="rounded-full bg-secondary/10 px-2 py-0.5 text-xs font-medium text-secondary">
                {fit}
              </span>
            )}
            {odds && <WordTag label="Odds" word={odds} tone="odds" />}
          </div>
        )}
      </div>
      {reason && <div className="mt-1 text-xs text-muted-foreground">{reason}</div>}
    </div>
  )
}

export default function SchoolList() {
  const { data: matches = [] } = useQuery<MatchResultDual[]>({
    queryKey: ['matches'],
    queryFn: () => getMatches(),
  })

  const top = matches.slice(0, TOP_N)

  return (
    <div>
      <div className="mb-1 flex items-baseline justify-between gap-3">
        <div className="text-xs uppercase tracking-wide text-muted-foreground">Your school list</div>
        <Link to="/s/explore" className="text-xs font-medium text-secondary hover:underline">
          See all matches in Discover
        </Link>
      </div>
      <p className="mb-2 text-xs text-muted-foreground">
        Fit and odds are different — a reach can still be a great fit.
      </p>

      {top.length === 0 ? (
        <div className="text-sm text-muted-foreground">
          No matches yet — fill in your profile and Uni will build your list.
        </div>
      ) : (
        <div className="space-y-2">
          {top.map(m => (
            <SchoolRow key={m.id} match={m} />
          ))}
        </div>
      )}
    </div>
  )
}
