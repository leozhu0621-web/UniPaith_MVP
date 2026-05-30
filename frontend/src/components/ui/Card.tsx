// Card — Spec/02-design-system.md §5.
// Default container for a program, school, application, message thread.
// Four variants: card (default surface + subtle elevation), card-flush
// (no elevation, nested grouping inside a wider card), card-raised
// (elev-raised, used for hover/dropdown/modal triggers), card-accent
// (elev-glow w/ 2px primary border — "this is THE focus" card. Rare).

import { forwardRef } from 'react'
import clsx from 'clsx'

export type CardVariant = 'card' | 'card-flush' | 'card-raised' | 'card-accent'
export type CardPadding = 'none' | 'sm' | 'md' | 'lg'

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: CardVariant
  padding?: CardPadding
  interactive?: boolean
  asChild?: boolean
}

const VARIANT_CLASSES: Record<CardVariant, string> = {
  card: 'bg-card text-card-foreground border border-border elev-subtle',
  'card-flush': 'bg-background text-card-foreground border border-border',
  'card-raised': 'bg-card text-card-foreground elev-raised',
  'card-accent': 'bg-card text-card-foreground border-2 border-[#FFD60A] elev-glow dark:border-[#F2C800]',
}

// `sm` for compact program cards in a 4-col grid (16px); `md` default
// (24px); `lg` for hero cards (32px).
const PADDING_CLASSES: Record<CardPadding, string> = {
  none: '',
  sm: 'p-4',
  md: 'p-6',
  lg: 'p-8',
}

const Card = forwardRef<HTMLDivElement, CardProps>(
  (
    { variant = 'card', padding = 'md', interactive, className, children, ...props },
    ref,
  ) => {
    return (
      <div
        ref={ref}
        className={clsx(
          'rounded-[14px] motion-base transition-shadow',
          VARIANT_CLASSES[variant],
          PADDING_CLASSES[padding],
          interactive &&
            'cursor-pointer hover:elev-raised focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#FFD60A]',
          className,
        )}
        tabIndex={interactive ? 0 : undefined}
        {...props}
      >
        {children}
      </div>
    )
  },
)

Card.displayName = 'Card'

/** Optional named sub-regions — keeps structural order consistent across surfaces.
 *  Spec §5 Anatomy: Header (eyebrow + H3 + meta) → Body → Footer (actions). */
export function CardHeader({ className, children, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={clsx('flex flex-col gap-1', className)} {...props}>
      {children}
    </div>
  )
}

export function CardEyebrow({ className, children, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={clsx('up-eyebrow', className)} {...props}>
      {children}
    </div>
  )
}

export function CardTitle({ className, children, ...props }: React.HTMLAttributes<HTMLHeadingElement>) {
  return (
    <h3 className={clsx('text-[20px] leading-[1.3] font-bold', className)} {...props}>
      {children}
    </h3>
  )
}

export function CardBody({ className, children, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={clsx('mt-3 text-base text-foreground/85 leading-[1.6]', className)} {...props}>
      {children}
    </div>
  )
}

export function CardFooter({ className, children, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={clsx('mt-4 flex items-center justify-end gap-2', className)} {...props}>
      {children}
    </div>
  )
}

export default Card
