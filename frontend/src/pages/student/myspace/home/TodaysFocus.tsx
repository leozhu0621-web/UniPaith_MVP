import { useNavigate } from 'react-router-dom'
import { ArrowRight, Compass, Sparkles } from 'lucide-react'
import Card from '../../../../components/ui/Card'
import Badge from '../../../../components/ui/Badge'
import ProgressBar from '../../../../components/ui/ProgressBar'
import type { NextAction } from './upNext'

const ACCENT: Record<NextAction['urgency'], string> = {
  danger: 'border-l-error',
  warning: 'border-l-warning',
  neutral: 'border-l-secondary',
}
const ICON_TONE: Record<NextAction['urgency'], string> = {
  danger: 'text-error',
  warning: 'text-warning',
  neutral: 'text-secondary',
}
const BADGE: Record<NextAction['urgency'], 'error' | 'warning' | 'neutral'> = {
  danger: 'error',
  warning: 'warning',
  neutral: 'neutral',
}

interface Props {
  action: NextAction | null
  onboardingComplete: boolean
}

/** The single most important action — "one focal point per view" (Spec
 *  2026-06-14 §Modules.1). Caught-up state is positive, never a dead string. */
export default function TodaysFocus({ action, onboardingComplete }: Props) {
  const navigate = useNavigate()

  if (!action) {
    const cta = onboardingComplete
      ? { label: 'Talk to Uni', to: '/s' }
      : { label: 'Keep building your profile', to: '/s/profile' }
    return (
      <Card pad={false} className="border-l-4 border-l-secondary p-5">
        <p className="flex items-center gap-1.5 text-sm font-semibold text-foreground">
          <Sparkles size={15} className="text-secondary" aria-hidden /> You're all caught up
        </p>
        <p className="mt-1 text-xs text-muted-foreground">Nothing urgent right now. A good moment to get ahead.</p>
        <button
          onClick={() => navigate(cta.to)}
          className="ui-btn mt-3 inline-flex items-center gap-1.5 rounded-md bg-secondary px-3 py-1.5 text-xs font-medium text-secondary-foreground"
        >
          <Compass size={13} /> {cta.label}
        </button>
      </Card>
    )
  }

  const Icon = action.icon
  return (
    <Card pad={false} className={`border-l-4 ${ACCENT[action.urgency]} p-5`}>
      <div className="flex items-start gap-3">
        <Icon size={20} className={`mt-0.5 shrink-0 ${ICON_TONE[action.urgency]}`} aria-hidden />
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <p className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">Today's focus</p>
            <Badge variant={BADGE[action.urgency]}>{action.chip}</Badge>
          </div>
          <button
            onClick={() => navigate(action.to)}
            className="mt-1 block text-left text-base font-semibold text-foreground hover:text-secondary"
          >
            {action.title}
          </button>
          <p className="mt-0.5 text-xs text-muted-foreground">{action.sub}</p>
          {action.readinessPct != null && (
            <ProgressBar value={action.readinessPct} label="Ready to submit" className="mt-2 max-w-xs" />
          )}
        </div>
        <button
          onClick={() => navigate(action.to)}
          aria-label={`Go: ${action.title}`}
          className="ui-btn mt-0.5 inline-flex shrink-0 items-center gap-1 rounded-md bg-secondary px-3 py-1.5 text-xs font-medium text-secondary-foreground"
        >
          Go <ArrowRight size={13} />
        </button>
      </div>
    </Card>
  )
}
