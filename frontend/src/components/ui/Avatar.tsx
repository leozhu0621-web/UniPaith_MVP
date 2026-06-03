import clsx from 'clsx'

interface AvatarProps {
  name: string
  src?: string
  size?: 'sm' | 'md' | 'lg'
  className?: string
}

const SIZE_MAP = {
  sm: 'w-7 h-7 text-xs',
  md: 'w-9 h-9 text-sm',
  lg: 'w-12 h-12 text-base',
}

// On-brand, restrained tint set (duotone-derived) instead of a rainbow palette.
const COLORS = [
  'bg-secondary/15 text-secondary',
  'bg-success-soft text-success',
  'bg-warning-soft text-warning',
  'bg-muted text-foreground',
  'bg-secondary text-secondary-foreground',
]

function hashColor(name: string): string {
  let hash = 0
  for (let i = 0; i < name.length; i++) {
    hash = name.charCodeAt(i) + ((hash << 5) - hash)
  }
  return COLORS[Math.abs(hash) % COLORS.length]
}

function getInitials(name: string): string {
  return name
    .split(' ')
    .map(p => p[0])
    .filter(Boolean)
    .slice(0, 2)
    .join('')
    .toUpperCase()
}

export default function Avatar({ name, src, size = 'md', className }: AvatarProps) {
  if (src) {
    return (
      <img
        src={src}
        alt={name}
        className={clsx('rounded-full object-cover', SIZE_MAP[size], className)}
      />
    )
  }

  return (
    <div
      className={clsx(
        'rounded-full flex items-center justify-center font-semibold',
        SIZE_MAP[size],
        hashColor(name),
        className
      )}
    >
      {getInitials(name)}
    </div>
  )
}
