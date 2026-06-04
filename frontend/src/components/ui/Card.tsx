import clsx from 'clsx'

// Card — Spec/02-design-system.md §5.
// Default `card`: surface bg, 1px border, subtle elevation, token radius.
// Variants: card-flush (nested), card-raised (hover/menus), card-accent (the rare focal card).
type CardVariant = 'card' | 'card-flush' | 'card-raised' | 'card-accent'

interface CardProps {
  children: React.ReactNode
  className?: string
  variant?: CardVariant
  onClick?: () => void
  interactive?: boolean
}

const VARIANT_CLASSES: Record<CardVariant, string> = {
  card: 'bg-card border border-border elev-subtle',
  'card-flush': 'bg-background border border-border',
  'card-raised': 'bg-card border border-transparent elev-raised',
  'card-accent': 'bg-card border-2 border-primary elev-glow',
}

export default function Card({ children, className, variant = 'card', onClick, interactive }: CardProps) {
  const clickable = Boolean(onClick) || interactive
  return (
    <div
      className={clsx(
        'rounded-lg',
        VARIANT_CLASSES[variant],
        clickable &&
          'cursor-pointer transition duration-200 ease-out hover:-translate-y-0.5 hover:border-secondary/40 hover:elev-raised focus-within:-translate-y-0.5 focus-within:border-secondary/40 focus-within:elev-raised',
        className
      )}
      onClick={onClick}
    >
      {children}
    </div>
  )
}
