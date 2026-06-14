import { useNavigate } from 'react-router-dom'
import { Check } from 'lucide-react'
import { STAGES, deriveStage, stageIndex, type StageInputs } from './journeyStage'

/** Horizontal Discover › Match › Apply › Decide track. The current stage is
 *  lit in cobalt; reached stages are filled; future stages muted. Chrome →
 *  cobalt, never gold (Spec 2026-06-14 §Modules.2b). */
export default function JourneyMap(props: StageInputs) {
  const navigate = useNavigate()
  const current = deriveStage(props)
  const curIdx = stageIndex(current)

  return (
    <div className="flex items-center gap-1" role="list" aria-label="Your journey">
      {STAGES.map((s, i) => {
        const reached = i <= curIdx
        const isCurrent = i === curIdx
        return (
          <div key={s.key} className="flex flex-1 items-center" role="listitem">
            <button
              onClick={() => navigate(s.to)}
              aria-current={isCurrent ? 'step' : undefined}
              className="group flex min-w-0 flex-shrink-0 flex-col items-center gap-1"
            >
              <span
                className={`flex h-6 w-6 items-center justify-center rounded-full text-[10px] font-bold transition-colors ${
                  isCurrent
                    ? 'bg-secondary text-secondary-foreground ring-2 ring-secondary/30'
                    : reached
                      ? 'bg-secondary/15 text-secondary'
                      : 'bg-muted text-muted-foreground'
                }`}
              >
                {reached && !isCurrent ? <Check size={12} /> : i + 1}
              </span>
              <span className={`text-[10px] font-medium ${isCurrent ? 'text-secondary' : reached ? 'text-foreground' : 'text-muted-foreground'}`}>
                {s.label}
              </span>
            </button>
            {i < STAGES.length - 1 && (
              <span className={`mx-1 h-0.5 flex-1 rounded-full ${i < curIdx ? 'bg-secondary/40' : 'bg-border'}`} />
            )}
          </div>
        )
      })}
    </div>
  )
}
