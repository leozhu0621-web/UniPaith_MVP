/**
 * In-thread "first look" at matches — Stage 02 Recommendation, peeked inside Uni.
 *
 * When the deterministic readiness verdict says the student is match-ready, Uni
 * delivers a recap + their top fits (real dual score + a one-line why) inline,
 * then hands off to the full Match surface ("Go deeper"). Reuses existing match
 * data + scores + rationale; no new backend, no grid/filters/compare here. The
 * `always` variant offers an honest "look anytime" card before readiness.
 */
import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { ArrowRight, Compass } from 'lucide-react'

import { getHandoffVerdict } from '../../../api/discovery'
import { getMatches } from '../../../api/matching'
import Button from '../../../components/ui/Button'
import type { HandoffVerdict, MatchResultDual } from '../../../types'
import DualRing from '../match/DualRing'

interface Props {
  /** Pass an already-fetched verdict to skip the query (used in the thread). */
  verdict?: HandoffVerdict
  /** `auto` renders only when ready; `always` shows a look-anytime card too. */
  variant?: 'auto' | 'always'
  onKeepTalking?: () => void
}

export default function FirstLookCard({ verdict: verdictProp, variant = 'auto', onKeepTalking }: Props) {
  const navigate = useNavigate()
  const { data: fetched, isFetching } = useQuery<HandoffVerdict>({
    queryKey: ['discovery', 'handoff'],
    queryFn: getHandoffVerdict,
    enabled: verdictProp === undefined,
  })
  const verdict = verdictProp ?? fetched
  const ready = !!verdict?.should_handoff

  // Only pull matches once the student is ready — the first look is the reward
  // for covering the three Discovery stages.
  const { data: matches = [] } = useQuery<MatchResultDual[]>({
    queryKey: ['matches', 'first-look'],
    queryFn: () => getMatches(false),
    enabled: ready,
  })
  const top = matches.slice(0, 3)

  if (variant === 'auto' && !ready) return null
  // Hold the card back while a verdict fetch is in flight so a stale verdict
  // can't flash the wrong copy at the moment readiness may have flipped.
  if (verdictProp === undefined && isFetching) return null

  return (
    <div className="flex gap-2.5" data-testid="first-look-card">
      <div className="h-7 w-7 rounded-full bg-secondary text-white flex items-center justify-center shrink-0 mt-0.5 text-xs font-semibold">
        U
      </div>
      <div className="flex-1 rounded-2xl rounded-bl-sm border border-secondary/30 bg-secondary/5 px-4 py-3 max-w-[88%]">
        <p className="text-sm leading-relaxed text-foreground">
          {ready ? (
            <>
              I think I know you well enough to show you something — a first look at where you'd
              genuinely thrive, not just where you can get in.
            </>
          ) : (
            <>
              We can look at programs whenever you like. The more we talk, the sharper your matches
              get — but there's no wrong time to start.
            </>
          )}
        </p>

        {ready && top.length > 0 && (
          <div className="mt-3 rounded-xl border border-border bg-card divide-y divide-border overflow-hidden">
            {top.map(m => {
              const why = m.rationale_text || ''
              // Grounded facts straight from the catalog — real cost + selectivity.
              const facts = [
                m.tuition ? `$${m.tuition.toLocaleString()}/yr` : null,
                m.acceptance_rate != null ? `${Math.round(m.acceptance_rate * 100)}% admit` : null,
                m.band_label ? `${m.band_label} fit` : null,
              ]
                .filter(Boolean)
                .join(' · ')
              return (
                <div key={m.program_id} className="flex items-center gap-3 px-3 py-2.5">
                  <DualRing
                    fitness={Number(m.fitness_score)}
                    confidence={Number(m.confidence_score)}
                    size={38}
                    compact
                  />
                  <div className="min-w-0 flex-1">
                    <div className="text-sm font-medium text-foreground truncate">
                      {m.program_name}
                      {m.institution_name ? ` · ${m.institution_name}` : ''}
                    </div>
                    {facts && <div className="text-xs text-muted-foreground">{facts}</div>}
                    {why && <div className="text-xs text-muted-foreground line-clamp-2">{why}</div>}
                  </div>
                </div>
              )
            })}
            <div className="px-3 py-2 text-xs text-muted-foreground bg-muted/40">
              These sharpen the more we talk — and there are more where these came from.
            </div>
          </div>
        )}

        <div className="mt-3 flex flex-wrap items-center gap-2">
          <Button variant="secondary" size="sm" onClick={() => navigate('/s/explore')}>
            <Compass size={14} className="mr-1.5" />
            {ready ? 'Go deeper in Match' : 'See programs that fit me'}
            <ArrowRight size={14} className="ml-1" />
          </Button>
          {onKeepTalking && (
            <button
              type="button"
              onClick={onKeepTalking}
              className="text-xs text-muted-foreground hover:text-foreground transition-colors"
            >
              Keep talking
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
