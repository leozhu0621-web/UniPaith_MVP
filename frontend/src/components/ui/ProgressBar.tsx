import clsx from 'clsx'

interface ProgressBarProps {
  value: number // 0-100
  label?: string
  className?: string
}

export default function ProgressBar({ value, label, className }: ProgressBarProps) {
  const clamped = Math.max(0, Math.min(100, value))
  return (
    <div className={clsx('w-full', className)}>
      {label && (
        <div className="flex justify-between mb-1">
          <span className="text-xs text-muted-foreground">{label}</span>
          <span className="text-xs text-muted-foreground tabular-nums">{Math.round(clamped)}%</span>
        </div>
      )}
      <div
        className="w-full bg-muted rounded-pill h-2 overflow-hidden"
        role="progressbar"
        aria-valuenow={Math.round(clamped)}
        aria-valuemin={0}
        aria-valuemax={100}
      >
        <div
          className="bg-secondary h-2 rounded-pill transition-all duration-300"
          style={{ width: `${clamped}%` }}
        />
      </div>
    </div>
  )
}
