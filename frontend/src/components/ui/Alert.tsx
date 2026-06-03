import { useState } from 'react'
import clsx from 'clsx'
import { X, CheckCircle, AlertTriangle, AlertCircle, Info } from 'lucide-react'

// Alert — Spec/02-design-system.md §11. Persistent inline banner, full-width of
// its container. Use for page-level notices ("Your trial ends in 3 days").
type AlertVariant = 'success' | 'warning' | 'error' | 'info'

interface AlertProps {
  variant?: AlertVariant
  title?: string
  children?: React.ReactNode
  dismissible?: boolean
  action?: React.ReactNode
  className?: string
}

const STYLE: Record<AlertVariant, { wrap: string; icon: React.ReactNode }> = {
  success: { wrap: 'bg-success-soft/60 border-success/40 text-foreground', icon: <CheckCircle size={18} className="text-success" /> },
  warning: { wrap: 'bg-warning-soft/60 border-warning/40 text-foreground', icon: <AlertTriangle size={18} className="text-warning" /> },
  error: { wrap: 'bg-error-soft/60 border-error/40 text-foreground', icon: <AlertCircle size={18} className="text-error" /> },
  info: { wrap: 'bg-secondary/10 border-secondary/30 text-foreground', icon: <Info size={18} className="text-secondary" /> },
}

export default function Alert({ variant = 'info', title, children, dismissible, action, className }: AlertProps) {
  const [open, setOpen] = useState(true)
  if (!open) return null
  const style = STYLE[variant]
  return (
    <div role="alert" className={clsx('flex items-start gap-3 w-full rounded-lg border px-4 py-3', style.wrap, className)}>
      <span className="mt-0.5 shrink-0">{style.icon}</span>
      <div className="flex-1 min-w-0">
        {title && <p className="text-sm font-semibold text-foreground">{title}</p>}
        {children && <div className={clsx('text-sm text-muted-foreground', title && 'mt-0.5')}>{children}</div>}
      </div>
      {action && <div className="shrink-0">{action}</div>}
      {dismissible && (
        <button
          onClick={() => setOpen(false)}
          aria-label="Dismiss"
          className="p-0.5 -mr-0.5 rounded hover:bg-muted text-muted-foreground hover:text-foreground transition-colors shrink-0"
        >
          <X size={16} />
        </button>
      )}
    </div>
  )
}
