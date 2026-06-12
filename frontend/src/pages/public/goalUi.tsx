import type { ReactNode } from 'react'
import { ArrowRight } from 'lucide-react'

import Button from '../../components/ui/Button'
import Card from '../../components/ui/Card'

// Spec 48/49/50 — shared presentation for the /goal transparency pages.
// On-brand: Europa type scale, semantic dark-safe tokens, cobalt as the
// workhorse accent, success/warning via their soft+dark variants, and at most
// one Sunlit-Gold beat per page. No decorative gradients.

export type Tone = 'neutral' | 'cobalt' | 'gold' | 'success' | 'warning'

const TONE_CLASSES: Record<Tone, string> = {
  neutral: 'bg-muted text-muted-foreground',
  cobalt: 'bg-secondary/10 text-secondary',
  gold: 'border border-primary/40 text-foreground',
  success: 'bg-success-soft text-success dark:bg-success-dark-soft dark:text-success-dark',
  warning: 'bg-warning-soft text-warning dark:bg-warning-dark-soft dark:text-warning-dark',
}

export function Chip({
  children,
  tone = 'neutral',
  icon: Icon,
}: {
  children: ReactNode
  tone?: Tone
  icon?: typeof ArrowRight
}) {
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-pill px-2 py-0.5 text-[11px] font-semibold ${TONE_CLASSES[tone]}`}
    >
      {tone === 'gold' && <span className="h-1.5 w-1.5 rounded-full bg-primary" aria-hidden />}
      {Icon && <Icon size={11} className="shrink-0" />}
      {children}
    </span>
  )
}

export function GoalShell({ children }: { children: ReactNode }) {
  return (
    <div className="mx-auto max-w-6xl px-4 py-12 sm:px-6 sm:py-16 animate-page-in">{children}</div>
  )
}

export function Hero({
  eyebrow,
  title,
  lede,
  children,
}: {
  eyebrow: string
  title: ReactNode
  lede: ReactNode
  children?: ReactNode
}) {
  return (
    <header className="max-w-3xl">
      <p className="text-eyebrow font-semibold uppercase tracking-[0.22em] text-secondary">
        {eyebrow}
      </p>
      <h1 className="mt-3 text-h1 text-foreground sm:text-display">{title}</h1>
      <p className="mt-5 text-lg text-muted-foreground">{lede}</p>
      {children && <div className="mt-6 flex flex-wrap items-center gap-3">{children}</div>}
    </header>
  )
}

export function Stat({ value, label }: { value: ReactNode; label: string }) {
  return (
    <div>
      <div className="text-h1 leading-none text-foreground">{value}</div>
      <div className="mt-1.5 text-sm text-muted-foreground">{label}</div>
    </div>
  )
}

export function StatBand({ children, isError }: { children: ReactNode; isError?: boolean }) {
  return (
    <section className="mt-10 grid grid-cols-2 gap-6 rounded-xl border border-border bg-card p-6 sm:grid-cols-4 sm:p-8">
      {isError ? (
        <p className="col-span-2 text-sm text-muted-foreground sm:col-span-4">
          The live headline numbers couldn&rsquo;t be loaded just now.
        </p>
      ) : (
        children
      )}
    </section>
  )
}

export function StatSkeleton() {
  return <div className="h-16 rounded-lg bg-muted animate-pulse" />
}

export function CardSkeleton({ className = 'h-40' }: { className?: string }) {
  return <div className={`${className} rounded-lg border border-border bg-card animate-pulse`} />
}

export function SectionHeading({
  icon: Icon,
  title,
  sub,
}: {
  icon?: typeof ArrowRight
  title: string
  sub?: ReactNode
}) {
  return (
    <div>
      <div className="flex items-center gap-2">
        {Icon && <Icon className="text-secondary" size={20} />}
        <h2 className="text-h2 text-foreground">{title}</h2>
      </div>
      {sub && <p className="mt-2 max-w-2xl text-muted-foreground">{sub}</p>}
    </div>
  )
}

// Card heading — a real <h3> so screen-reader heading navigation reaches the
// card's core content (previously these were rendered as a styled <span>, which
// silently dropped them from the heading outline). Inline-flex keeps an optional
// leading icon (or a caller-supplied badge passed as children) on the same line.
export function CardTitle({
  children,
  icon: Icon,
  className = '',
}: {
  children: ReactNode
  icon?: typeof ArrowRight
  className?: string
}) {
  return (
    <h3 className={`inline-flex items-center gap-2 text-h3 text-foreground ${className}`}>
      {Icon && <Icon size={18} className="shrink-0 text-secondary" />}
      {children}
    </h3>
  )
}

export function ErrorState({ onRetry, label }: { onRetry: () => void; label?: string }) {
  return (
    <Card pad={false} className="mt-6 p-8 text-center">
      <p className="text-foreground">{label ?? "We couldn't load this just now."}</p>
      <Button variant="secondary" className="mt-4" onClick={onRetry}>
        Retry
      </Button>
    </Card>
  )
}

// Filter pill row — cobalt active state, identical to the AI-agents page.
export function FilterRow({
  options,
  value,
  onChange,
}: {
  options: { key: string; label: string }[]
  value: string
  onChange: (k: string) => void
}) {
  return (
    <div className="flex flex-wrap gap-2">
      {options.map(o => {
        const active = o.key === value
        return (
          <button
            key={o.key}
            type="button"
            onClick={() => onChange(o.key)}
            aria-pressed={active}
            className={
              'rounded-pill px-3 py-1 text-[13px] font-semibold transition-colors ' +
              'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-secondary ' +
              (active
                ? 'bg-secondary text-secondary-foreground'
                : 'border border-border bg-card text-muted-foreground hover:bg-muted')
            }
          >
            {o.label}
          </button>
        )
      })}
    </div>
  )
}
