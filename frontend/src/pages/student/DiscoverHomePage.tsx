/**
 * Stage 1 (Discovery) — the Uni guided workspace.
 *
 * A ChatGPT/Claude-style two-pane shell: a left JourneyRail (the three Discovery
 * stages + a "first look" matches item + the living profile) and the center
 * conversation, which Uni leads stage-by-stage. On mobile the rail folds into a
 * slim journey bar that opens a bottom sheet, so the conversation owns the
 * screen. The rail drives the conversation through an imperative `ask`.
 */
import { useCallback, useMemo, useRef, useState } from 'react'
import { ChevronDown, Sparkles } from 'lucide-react'

import Card from '../../components/ui/Card'
import Sheet from '../../components/ui/Sheet'
import { useAuthStore } from '../../stores/auth-store'
import JourneyRail from './discover/JourneyRail'
import LivingProfilePanel from './discover/LivingProfilePanel'
import UniConversation from './discover/UniConversation'
import { useJourneyState, type StageKey } from './discover/useJourneyState'

export default function DiscoverHomePage() {
  const [profileOpen, setProfileOpen] = useState(false)
  const [journeySheetOpen, setJourneySheetOpen] = useState(false)
  const askRef = useRef<(t: string) => void>(() => {})
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
      <div className="p-4 lg:p-6 mx-auto max-w-6xl w-full">
        <Card className="p-4 sm:p-5">
          <UniConversation
            profileOpen={profileOpen}
            onProfileOpenChange={setProfileOpen}
            onReady={onReady}
          />
        </Card>
      </div>
    )
  }

  return (
    <div className="p-4 lg:p-6 w-full">
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
          <JourneyRail {...railProps} />
        </aside>

        <div className="flex min-w-0 flex-1 justify-center">
          <div className="w-full max-w-[720px]">
            <Card className="p-4 sm:p-5">
              <UniConversation
                guided
                profileOpen={profileOpen}
                onProfileOpenChange={setProfileOpen}
                onReady={onReady}
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
