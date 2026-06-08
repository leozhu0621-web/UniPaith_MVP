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
import JourneyRail from './discover/JourneyRail'
import UniConversation from './discover/UniConversation'
import { useJourneyState, type StageKey } from './discover/useJourneyState'

export default function DiscoverHomePage() {
  const [profileOpen, setProfileOpen] = useState(false)
  const [journeySheetOpen, setJourneySheetOpen] = useState(false)
  const askRef = useRef<(t: string) => void>(() => {})
  const journey = useJourneyState(true)

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

  return (
    <div className="p-4 lg:p-6 mx-auto max-w-6xl w-full">
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

      <div className="flex gap-6">
        <aside className="hidden lg:block w-64 shrink-0">
          <JourneyRail {...railProps} />
        </aside>

        <div className="flex-1 min-w-0">
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
