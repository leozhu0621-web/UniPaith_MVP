import Badge from '../../../components/ui/Badge'
import type { FairnessSeverity } from '../../../api/fairness'

const ATTRIBUTE_LABELS: Record<string, string> = {
  gender: 'Gender',
  first_gen: 'First-generation',
  international: 'International',
  nationality_region: 'Nationality',
  veteran: 'Veteran',
  race: 'Race / ethnicity',
  disability: 'Disability',
}

export function attributeLabel(attr: string): string {
  return ATTRIBUTE_LABELS[attr] ?? attr.replace(/_/g, ' ')
}

const SEVERITY_META: Record<
  FairnessSeverity,
  { variant: 'success' | 'warning' | 'error' | 'info' | 'neutral'; label: string }
> = {
  info: { variant: 'success', label: 'Fair' },
  warning: { variant: 'warning', label: 'Watch' },
  high: { variant: 'error', label: 'Breach' },
  auto_halt: { variant: 'error', label: 'Halted' },
  override_active: { variant: 'info', label: 'Override' },
}

export function severityBadge(severity: FairnessSeverity) {
  const meta = SEVERITY_META[severity] ?? SEVERITY_META.info
  return <Badge variant={meta.variant}>{meta.label}</Badge>
}

/** Severity → an accessible dot color class (for compact heatmap cells). */
export function severityDotClass(severity: FairnessSeverity, sufficient: boolean): string {
  if (!sufficient) return 'bg-muted'
  switch (severity) {
    case 'auto_halt':
    case 'high':
      return 'bg-error'
    case 'warning':
      return 'bg-warning'
    case 'override_active':
      return 'bg-secondary'
    default:
      return 'bg-success'
  }
}
