/**
 * The Uni journey rail — Stage 01 Discovery stages (with progress/locked/done),
 * a Stage 02 "first look" matches item, and the living profile. Docked left on
 * desktop (≥ lg); rendered inside a bottom sheet on mobile. Stage math comes from
 * useJourneyState; revisiting a done stage nudges the conversation via onRevisit.
 */
import clsx from 'clsx'
import { Check, Lock, Sparkles } from 'lucide-react'

import LivingProfilePanel from './LivingProfilePanel'
import type { JourneyStage, StageKey } from './useJourneyState'

function StageDot({ state }: { state: JourneyStage['state'] }) {
  if (state === 'done')
    return (
      <span className="w-4 h-4 rounded-full bg-secondary text-white flex items-center justify-center shrink-0">
        <Check size={10} />
      </span>
    )
  if (state === 'current')
    return <span className="w-4 h-4 rounded-full border-2 border-secondary shrink-0" />
  return (
    <span className="w-4 h-4 rounded-full border border-border flex items-center justify-center shrink-0 text-muted-foreground">
      <Lock size={9} />
    </span>
  )
}

export default function JourneyRail({
  stages,
  matchesUnlocked,
  onRevisit,
  onOpenMatches,
  onAsk,
}: {
  stages: JourneyStage[]
  matchesUnlocked: boolean
  onRevisit?: (key: StageKey) => void
  onOpenMatches?: () => void
  onAsk?: (prompt: string) => void
}) {
  return (
    <div className="flex flex-col gap-6 text-sm">
      <div>
        <p className="text-eyebrow text-muted-foreground mb-3">Stage 01 · Discovery</p>
        <div className="flex flex-col gap-1.5">
          {stages.map(s => {
            const done = s.state === 'done'
            const current = s.state === 'current'
            return (
              <button
                key={s.key}
                type="button"
                disabled={!done}
                onClick={() => done && onRevisit?.(s.key)}
                className={clsx(
                  'flex items-center gap-2.5 rounded-lg px-2.5 py-2 text-left transition-colors',
                  current &&
                    'bg-secondary/10 border border-secondary/30 font-medium text-foreground',
                  done && 'hover:bg-muted text-foreground',
                  s.state === 'locked' && 'text-muted-foreground cursor-default',
                )}
              >
                <StageDot state={s.state} />
                <span className="flex-1">{s.label}</span>
                {current && <span className="text-xs text-secondary">now</span>}
              </button>
            )
          })}
        </div>
      </div>

      <div>
        <p className="text-eyebrow text-muted-foreground mb-2">Stage 02 · a first look</p>
        <button
          type="button"
          disabled={!matchesUnlocked}
          onClick={() => matchesUnlocked && onOpenMatches?.()}
          className={clsx(
            'flex items-center gap-2.5 w-full rounded-lg px-2.5 py-2 text-left',
            matchesUnlocked
              ? 'text-secondary hover:bg-muted border border-dashed border-secondary/40'
              : 'text-muted-foreground cursor-default',
          )}
        >
          <Sparkles size={15} className="shrink-0" />
          <span className="flex-1">Your matches</span>
          {!matchesUnlocked && <span className="text-xs">unlocks soon</span>}
        </button>
      </div>

      {/* Living profile shows in the rail on mobile (sheet) + lg; at xl+ it moves
          to its own right column in DiscoverHomePage, so hide it here then. */}
      <div className="border-t border-border pt-4 xl:hidden">
        <p className="text-eyebrow text-muted-foreground mb-3">What Uni knows about you</p>
        <LivingProfilePanel onAsk={onAsk} />
      </div>
    </div>
  )
}
