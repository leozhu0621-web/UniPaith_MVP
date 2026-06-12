import { ChevronRight, Calendar, FileText, MessageSquare, Send } from 'lucide-react'
import Card from '../../../components/ui/Card'
import { formatDate } from '../../../utils/format'
import { differenceInDays } from 'date-fns'

interface Step {
  icon: any
  label: string
  hint?: string
  // When true, the factual-qualifier hint (e.g. deadline countdown, event date)
  // is shown only on hover via title, not as visible caption text.
  hintAsTooltip?: boolean
  tone: 'urgent' | 'primary' | 'info'
  onClick: () => void
}

interface Props {
  applicationDeadline?: string | null
  upcomingEvent?: {
    title: string
    event_datetime: string
    onClick: () => void
  } | null
  hasApplication?: boolean
  onApply?: () => void
  onViewApplication?: () => void
  onRequestInfo?: () => void
  onAskCounselor?: () => void
}

const TONE_STYLES = {
  urgent: 'bg-warning-soft hover:bg-warning-soft/70 border-warning/40 text-warning',
  primary: 'bg-secondary text-secondary-foreground hover:brightness-95 border-transparent',
  info: 'bg-muted/60 hover:bg-muted border-border/50 text-foreground',
}

export default function NextStepsCard({
  applicationDeadline,
  upcomingEvent,
  hasApplication,
  onApply,
  onViewApplication,
  onRequestInfo,
  onAskCounselor,
}: Props) {
  const steps: Step[] = []

  // Primary: Apply or View Application
  if (hasApplication && onViewApplication) {
    steps.push({
      icon: FileText,
      label: 'View your application',
      hint: 'Continue where you left off',
      tone: 'primary',
      onClick: onViewApplication,
    })
  } else if (onApply) {
    const daysLeft = applicationDeadline ? differenceInDays(new Date(applicationDeadline), new Date()) : null
    steps.push({
      icon: Send,
      label: 'Start your application',
      hint: daysLeft != null && daysLeft > 0
        ? `${daysLeft} days until deadline (${formatDate(applicationDeadline!)})`
        : applicationDeadline
          ? `Deadline: ${formatDate(applicationDeadline!)}`
          : 'Apply when you\'re ready',
      hintAsTooltip: true,
      tone: daysLeft != null && daysLeft <= 30 ? 'urgent' : 'primary',
      onClick: onApply,
    })
  }

  // Upcoming event
  if (upcomingEvent) {
    steps.push({
      icon: Calendar,
      label: upcomingEvent.title,
      hint: formatDate(upcomingEvent.event_datetime),
      hintAsTooltip: true,
      tone: 'info',
      onClick: upcomingEvent.onClick,
    })
  }

  // Ask counselor
  if (onAskCounselor) {
    steps.push({
      icon: MessageSquare,
      label: 'Ask your counselor',
      hint: 'Get a personalized take on this program',
      tone: 'info',
      onClick: onAskCounselor,
    })
  }

  // Request info
  if (onRequestInfo) {
    steps.push({
      icon: FileText,
      label: 'Request info from program',
      hint: 'Connect with admissions',
      tone: 'info',
      onClick: onRequestInfo,
    })
  }

  if (steps.length === 0) return null

  return (
    <Card pad={false} className="p-5">
      <div className="flex items-center gap-2 mb-3">
        <ChevronRight size={14} className="text-secondary" />
        <h3 className="font-semibold text-foreground">Next Steps</h3>
      </div>
      <div className="space-y-2">
        {steps.map((step, i) => (
          <button
            key={i}
            onClick={step.onClick}
            title={step.hintAsTooltip ? step.hint || undefined : undefined}
            className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg border transition-colors text-left ${TONE_STYLES[step.tone]}`}
          >
            <div className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 ${
              step.tone === 'primary' ? 'bg-secondary-foreground/20' : 'bg-card'
            }`}>
              <step.icon size={14} />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-xs font-semibold leading-tight">{step.label}</p>
              {step.hint && !step.hintAsTooltip && <p className={`text-[10px] mt-0.5 truncate ${
                step.tone === 'primary' ? 'text-secondary-foreground/80' : 'opacity-70'
              }`}>{step.hint}</p>}
            </div>
            <ChevronRight size={14} className="flex-shrink-0 opacity-60" />
          </button>
        ))}
      </div>
    </Card>
  )
}
