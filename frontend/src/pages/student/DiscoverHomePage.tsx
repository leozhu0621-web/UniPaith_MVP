/**
 * Stage 1 (Discovery) — the Uni guided workspace.
 *
 * A ChatGPT/Claude-style two-pane shell: a left JourneyRail (the three Discovery
 * stages + a "first look" matches item + the living profile) and the center
 * conversation, which Uni leads stage-by-stage. On mobile the rail folds into a
 * slim journey bar that opens a bottom sheet, so the conversation owns the
 * screen. The rail drives the conversation through an imperative `ask`.
 */
import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { ChevronDown, Sparkles } from 'lucide-react'

import Card from '../../components/ui/Card'
import Coachmark from '../../components/ui/Coachmark'
import Sheet from '../../components/ui/Sheet'
import { useAuthStore } from '../../stores/auth-store'
import JourneyRail from './discover/JourneyRail'
import LivingProfilePanel from './discover/LivingProfilePanel'
import UniConversation from './discover/UniConversation'
import { useJourneyState, type StageKey } from './discover/useJourneyState'

interface DiscoverHomePageProps {
  /**
   * When true the component is rendered inside ChatTabShell, which already
   * provides a session-browser left rail. In that mode we suppress:
   *   • JourneyRail  — the session browser is the navigation now.
   *   • LivingProfilePanel  — the right "What Uni knows about you" dashboard
   *     (rejected as CRM-feeling; profile lives in My Space).
   *   • The mobile journey bar / bottom sheet (no journey chrome at all).
   * The conversation column widens to fill the available center space.
   * Default: false — all existing routes are unaffected.
   */
  chatTabMode?: boolean
}

export default function DiscoverHomePage({ chatTabMode = false }: DiscoverHomePageProps) {
  const [profileOpen, setProfileOpen] = useState(false)
  const [journeySheetOpen, setJourneySheetOpen] = useState(false)
  const askRef = useRef<(t: string) => void>(() => {})

  // Cross-sell hand-off: writers ("Ask counselor" on a program/school/institution,
  // the review CTA, the Discover search empty state) navigate to
  // /s?prefill=<question>. Capture it once on mount and strip it from the URL so a
  // refresh / back-nav doesn't silently re-ask. UniConversation sends it as the
  // opening student turn once the session resolves.
  const [searchParams, setSearchParams] = useSearchParams()
  const [prefill] = useState(() => searchParams.get('prefill') || undefined)
  useEffect(() => {
    if (!searchParams.has('prefill')) return
    const next = new URLSearchParams(searchParams)
    next.delete('prefill')
    setSearchParams(next, { replace: true })
    // Run once on mount — the captured `prefill` outlives the cleared param.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])
  // Guided workspace shell is gated on the backend ai_uni_guided_v1 flag
  // (spec §9). Flag off → the prior single-column open Uni experience (no rail,
  // no journey chrome) so nothing regresses.
  const guided = !!useAuthStore(s => s.user?.uni_guided)
  const journey = useJourneyState(guided)

  const onReady = useCallback((api: { ask: (t: string) => void }) => {
    askRef.current = api.ask
  }, [])

  const railProps = useMemo(
    () => ({
      stages: journey.stages,
      matchesUnlocked: journey.matchesUnlocked,
      onRevisit: (key: StageKey) => {
        const label = journey.stages.find(s => s.key === key)?.label ?? 'that'
        askRef.current(`Let's revisit ${label}.`)
        setJourneySheetOpen(false)
      },
      onOpenMatches: () => {
        askRef.current('Can I see a first look at my matches?')
        setJourneySheetOpen(false)
      },
      onAsk: (p: string) => {
        askRef.current(p)
        setJourneySheetOpen(false)
      },
    }),
    [journey.stages, journey.matchesUnlocked],
  )

  // Flag off — single-column open Uni, no guided chrome (spec §9 fallback).
  if (!guided) {
    return (
      <div className="p-4 lg:p-6 mx-auto max-w-6xl w-full animate-page-in">
        <Card pad={false} className="p-4 sm:p-5">
          <UniConversation
            profileOpen={profileOpen}
            onProfileOpenChange={setProfileOpen}
            onReady={onReady}
            prefill={prefill}
          />
        </Card>
      </div>
    )
  }

  // chatTabMode: suppress all journey/profile chrome — the session browser in
  // ChatTabShell is the navigation; the profile lives in My Space. The
  // conversation widens to fill the available center space (still
  // max-w-[720px] so it reads as a comfortable warm column, not edge-to-edge).
  if (chatTabMode) {
    return (
      <div className="p-4 lg:p-6 w-full animate-page-in">
        <div className="flex min-w-0 flex-1 justify-center">
          <div className="w-full max-w-[720px]">
            <Card pad={false} className="p-4 sm:p-5">
              <UniConversation
                guided
                profileOpen={profileOpen}
                onProfileOpenChange={setProfileOpen}
                onReady={onReady}
                prefill={prefill}
              />
            </Card>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="p-4 lg:p-6 w-full animate-page-in">
      {/* Mobile journey bar — opens the rail as a bottom sheet. */}
      <button
        type="button"
        onClick={() => setJourneySheetOpen(true)}
        className="lg:hidden mb-3 flex w-full items-center justify-between gap-3 rounded-lg border border-border bg-card px-3.5 py-2.5 text-left"
      >
        <span className="flex items-center gap-2 text-sm">
          <Sparkles size={15} className="text-secondary shrink-0" />
          <span className="font-medium text-foreground">
            {journey.currentStage?.label ?? 'Your journey'}
          </span>
          <span className="text-muted-foreground">· journey &amp; profile</span>
        </span>
        <ChevronDown size={16} className="text-muted-foreground shrink-0" />
      </button>

      <div className="flex gap-6 xl:gap-8">
        <aside className="hidden lg:block w-60 shrink-0">
          {/* minViewport: the rail is CSS-hidden below lg — keep the mark out of the queue there. */}
          <Coachmark id="uni-journey" title="Journey rail" body="Uni walks you through Profile, Goals, and Needs." placement="right" minViewport="lg">
            <JourneyRail {...railProps} />
          </Coachmark>
        </aside>

        <div className="flex min-w-0 flex-1 justify-center">
          <div className="w-full max-w-[720px]">
            <Card pad={false} className="p-4 sm:p-5">
              <UniConversation
                guided
                profileOpen={profileOpen}
                onProfileOpenChange={setProfileOpen}
                onReady={onReady}
                prefill={prefill}
              />
            </Card>
          </div>
        </div>

        {/* Living profile gets its own column at xl+ (it's xl:hidden in the rail,
            so it appears in exactly one place per breakpoint). */}
        <aside className="hidden xl:block w-72 shrink-0">
          <p className="text-eyebrow text-muted-foreground mb-3">What Uni knows about you</p>
          <LivingProfilePanel onAsk={railProps.onAsk} />
        </aside>
      </div>

      <Sheet
        isOpen={journeySheetOpen}
        onClose={() => setJourneySheetOpen(false)}
        title="Your journey"
        side="bottom"
      >
        <JourneyRail {...railProps} />
      </Sheet>
    </div>
  )
}
