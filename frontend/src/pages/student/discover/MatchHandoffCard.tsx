/**
 * In-thread, counselor-led match handoff (Task 8 / spec §3.5).
 *
 * Uni offers the handoff in her own voice when the deterministic readiness
 * verdict says the student is match-ready — no progress bar, no "100% complete"
 * gate. An `always` variant lets the student look anytime, with an honest note
 * that the matches sharpen the more they talk. Navigation reuses the existing
 * /s/explore (Match) flow; nothing about matching or strategy changes here.
 */
import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { ArrowRight, Compass } from 'lucide-react'

import { getHandoffVerdict } from '../../../api/discovery'
import Button from '../../../components/ui/Button'
import type { HandoffVerdict } from '../../../types'

interface Props {
  /** Pass an already-fetched verdict to skip the query (used in the thread). */
  verdict?: HandoffVerdict
  /**
   * `auto` renders only when the student is match-ready (in-thread offer);
   * `always` renders an ever-present "look anytime" card with a confidence note.
   */
  variant?: 'auto' | 'always'
  onKeepTalking?: () => void
}

export default function MatchHandoffCard({ verdict: verdictProp, variant = 'auto', onKeepTalking }: Props) {
  const navigate = useNavigate()
  const { data: fetched, isFetching } = useQuery<HandoffVerdict>({
    queryKey: ['discovery', 'handoff'],
    queryFn: getHandoffVerdict,
    enabled: verdictProp === undefined,
  })
  const verdict = verdictProp ?? fetched
  const ready = !!verdict?.should_handoff

  if (variant === 'auto' && !ready) return null
  // Hold the card back while any fetch is in flight (including background
  // refetches after a chat-turn invalidation) so a stale verdict can't show
  // the wrong copy at the moment readiness may have flipped.
  if (verdictProp === undefined && isFetching) return null

  return (
    <div className="flex gap-2.5" data-testid="match-handoff-card">
      <div className="h-7 w-7 rounded-full bg-secondary text-white flex items-center justify-center shrink-0 mt-0.5 text-xs font-semibold">
        U
      </div>
      <div className="flex-1 rounded-2xl rounded-bl-sm border border-secondary/30 bg-secondary/5 px-4 py-3 max-w-[88%]">
        <p className="text-sm leading-relaxed text-foreground">
          {ready ? (
            <>
              I think I've got a real sense of you now. Want to see the programs that genuinely fit
              you — not just the ones you could get into?
            </>
          ) : (
            <>
              We can look at programs whenever you like. The more we talk, the sharper your matches
              get — but there's no wrong time to start.
            </>
          )}
        </p>
        <div className="mt-3 flex flex-wrap items-center gap-2">
          <Button variant="secondary" size="sm" onClick={() => navigate('/s/explore')}>
            <Compass size={14} className="mr-1.5" />
            See programs that fit me
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
