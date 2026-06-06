import type { LucideIcon } from 'lucide-react'
import clsx from 'clsx'
import Card from '../../../components/ui/Card'

// Shared section shell for Settings (Spec 21 §6 — plain, dense, editorial).
// No gold anywhere; danger sections use --error border/text only.

interface SettingsSectionProps {
  icon: LucideIcon
  title: string
  description?: string
  children: React.ReactNode
  tone?: 'default' | 'danger'
  action?: React.ReactNode
  id?: string
}

export default function SettingsSection({
  icon: Icon,
  title,
  description,
  children,
  tone = 'default',
  action,
  id,
}: SettingsSectionProps) {
  const danger = tone === 'danger'
  return (
    <div id={id}>
      <Card className={clsx('p-5 sm:p-6', danger && 'border-error/40')}>
        <div className="flex items-start justify-between gap-3 mb-4">
          <div className="flex items-start gap-3">
            <span
              className={clsx(
                'mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg',
                danger ? 'bg-error-soft text-error' : 'bg-muted text-secondary'
              )}
            >
              <Icon size={17} />
            </span>
            <div>
              <h2 className={clsx('text-base font-semibold', danger ? 'text-error' : 'text-foreground')}>
                {title}
              </h2>
              {description && <p className="text-sm text-muted-foreground mt-0.5">{description}</p>}
            </div>
          </div>
          {action}
        </div>
        {children}
      </Card>
    </div>
  )
}

// A labelled row (label left, control/value right) used inside sections.
export function SettingRow({
  label,
  description,
  children,
  htmlFor,
}: {
  label: string
  description?: string
  children: React.ReactNode
  htmlFor?: string
}) {
  return (
    <div className="flex items-center justify-between gap-4 py-2.5">
      <div className="min-w-0">
        <label htmlFor={htmlFor} className="block text-sm font-medium text-foreground">
          {label}
        </label>
        {description && <p className="text-xs text-muted-foreground mt-0.5">{description}</p>}
      </div>
      <div className="shrink-0">{children}</div>
    </div>
  )
}
