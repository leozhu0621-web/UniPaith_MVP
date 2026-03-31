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
          <span className="text-xs text-gray-600">{label}</span>
          <span className="text-xs text-gray-500">{Math.round(clamped)}%</span>
        </div>
      )}
      <div className="w-full bg-gray-200 rounded-full h-2">
        <div
          className="bg-gray-900 h-2 rounded-full transition-all duration-300"
          style={{ width: `${clamped}%` }}
        />
      </div>
    </div>
  )
}
