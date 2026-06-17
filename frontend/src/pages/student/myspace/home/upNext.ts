import { AlertTriangle, Award, Calendar as CalendarIcon, Compass, PenLine } from 'lucide-react'
import type { Application } from '../../../../types'
import type { CalendarItem } from '../../../../api/calendar'

export type NextAction = {
  key: string
  icon: typeof PenLine
  title: string
  sub: string
  urgency: 'danger' | 'warning' | 'neutral'
  chip: string
  to: string
}

export interface UpNextInputs {
  calItems: CalendarItem[]
  offers: Application[]
  drafts: Application[]
  pendingClarifications: number
}

function programLabel(app: Application): string {
  return app.program?.program_name ?? 'your program'
}

/** Priority order across the cycle, capped at 5 (Spec 2026-06-10 §4). */
export function buildUpNext({ calItems, offers, drafts, pendingClarifications }: UpNextInputs): NextAction[] {
  const actions: NextAction[] = []
  for (const item of calItems.filter(i => i.status === 'overdue').slice(0, 2)) {
    actions.push({
      key: `overdue-${item.id}`,
      icon: AlertTriangle,
      title: item.title,
      sub: item.subtitle ?? item.institution_name ?? 'Overdue',
      urgency: 'danger',
      chip: 'overdue',
      to: '/s/calendar',
    })
  }
  for (const app of offers.filter(a => !a.student_decision)) {
    actions.push({
      key: `offer-${app.id}`,
      icon: Award,
      title: `Respond to your offer — ${programLabel(app)}`,
      sub: app.program?.institution_name ?? 'Decision needed',
      urgency: 'warning',
      chip: 'offer in',
      to: `/s/applications/${app.id}?tab=offer`,
    })
  }
  for (const item of calItems.filter(i => i.can_confirm)) {
    actions.push({
      key: `interview-${item.id}`,
      icon: CalendarIcon,
      title: item.title,
      sub: 'Pick a time that works for you',
      urgency: 'warning',
      chip: 'slots held',
      to: '/s/prep?tab=interviews',
    })
  }
  for (const app of drafts.slice().sort((a, b) => (b.readiness_pct ?? 0) - (a.readiness_pct ?? 0))) {
    actions.push({
      key: `draft-${app.id}`,
      icon: PenLine,
      title: `Continue ${programLabel(app)}`,
      sub: app.readiness_pct != null ? `${Math.round(app.readiness_pct)}% ready to submit` : 'In progress',
      urgency: 'neutral',
      chip: 'draft',
      to: `/s/applications/${app.id}`,
    })
  }
  if (pendingClarifications > 0) {
    actions.push({
      key: 'clarifications',
      icon: Compass,
      title: `Answer ${pendingClarifications} quick question${pendingClarifications === 1 ? '' : 's'} from Uni`,
      sub: 'Sharpens your matches and readiness',
      urgency: 'neutral',
      chip: 'quick win',
      to: '/s',
    })
  }
  return actions.slice(0, 5)
}
