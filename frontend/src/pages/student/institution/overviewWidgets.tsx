/* ──────────────────────────────────────────────────────────────────────────
   Overview visual primitives (Niche-style) — pure presentational components
   used by InstitutionDetail's OverviewTab. Self-contained: they format their
   own simple values and use semantic tokens only (dark-mode safe). Gold
   (`--primary`) is reserved for the single earned peak (the #1 ranking);
   everything else uses cobalt (`--secondary`).
   ────────────────────────────────────────────────────────────────────────── */
import { Fragment } from 'react'
import { Award, ChevronRight, ExternalLink } from 'lucide-react'

/** A single ranking as a medallion badge. `peak` (the #1) earns the gold beat.
 *  With `href`, the whole badge links to that ranking's reference page. */
export function RankingBadge({
  rank,
  label,
  year,
  peak = false,
  href,
}: {
  rank: number
  label: string
  year?: number
  peak?: boolean
  href?: string
}) {
  const cls = `flex items-center gap-3 rounded-xl border p-3.5 ${
    peak ? 'border-primary/40 bg-primary/[0.07]' : 'border-border bg-muted/40'
  }${href ? ' transition-colors hover:border-secondary' : ''}`
  const inner = (
    <>
      <div
        className={`flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-full ${
          peak ? 'bg-primary/15 text-primary' : 'bg-secondary/10 text-secondary'
        }`}
      >
        <Award size={18} />
      </div>
      <div className="min-w-0 flex-1">
        <p className="text-xl font-bold leading-none text-foreground tabular-nums">#{rank}</p>
        <p className="mt-1 truncate text-[12px] leading-snug text-muted-foreground">
          {label}
          {year ? ` · ${year}` : ''}
        </p>
      </div>
      {href && (
        <ExternalLink size={13} className="flex-shrink-0 text-muted-foreground/60" aria-hidden="true" />
      )}
    </>
  )
  if (href) {
    return (
      <a
        data-testid="ranking-badge"
        data-peak={peak ? 'true' : undefined}
        href={href}
        target="_blank"
        rel="noopener noreferrer"
        className={cls}
      >
        {inner}
      </a>
    )
  }
  return (
    <div data-testid="ranking-badge" data-peak={peak ? 'true' : undefined} className={cls}>
      {inner}
    </div>
  )
}

/** Applied → Admitted → Acceptance-rate strip. The rate step is the cobalt accent. */
export function AdmissionsFunnel({
  applicants,
  admits,
  rate,
  cycle,
}: {
  applicants: number
  admits: number
  rate: number
  cycle?: string
}) {
  const steps = [
    { value: applicants.toLocaleString(), label: 'Applied', accent: false },
    { value: admits.toLocaleString(), label: 'Admitted', accent: false },
    {
      value: `${(rate * 100).toFixed(rate < 0.1 ? 1 : 0)}%`,
      label: 'Acceptance rate',
      accent: true,
    },
  ]
  return (
    <div data-testid="admissions-funnel" title={cycle || undefined}>
      <div className="flex items-stretch gap-1.5">
        {steps.map((s, i) => (
          <Fragment key={s.label}>
            {i > 0 && (
              <div className="flex items-center text-border" aria-hidden="true">
                <ChevronRight size={16} />
              </div>
            )}
            <div
              className={`flex-1 rounded-lg border p-3 text-center ${
                s.accent ? 'border-secondary/40 bg-secondary/[0.06]' : 'border-border bg-muted/40'
              }`}
            >
              <p
                className={`text-lg font-bold leading-none tabular-nums ${
                  s.accent ? 'text-secondary' : 'text-foreground'
                }`}
              >
                {s.value}
              </p>
              <p className="mt-1 text-[11px] text-muted-foreground">{s.label}</p>
            </div>
          </Fragment>
        ))}
      </div>
    </div>
  )
}

/** A labeled horizontal progress bar for a single 0–1 proportion. */
export function StatBar({ label, pct, hint }: { label: string; pct: number; hint?: string }) {
  const w = Math.max(0, Math.min(100, pct * 100))
  return (
    <div>
      <div className="flex items-baseline justify-between gap-2">
        <span className="text-[12px] text-foreground/80">{label}</span>
        <span
          className="text-[13px] font-semibold tabular-nums text-foreground"
          title={hint || undefined}
        >
          {Math.round(w)}%
        </span>
      </div>
      <div
        className="mt-1 h-1.5 w-full overflow-hidden rounded-full bg-muted"
        role="img"
        aria-label={`${label}: ${Math.round(w)} percent`}
      >
        <div className="h-full rounded-full bg-secondary" style={{ width: `${w}%` }} />
      </div>
    </div>
  )
}

/** Segmented diversity bar + legend. Restrained cobalt-opacity palette (dark-safe). */
export function DiversityBar({ segments }: { segments: { label: string; pct: number }[] }) {
  const items = segments.filter(s => s.pct > 0)
  if (!items.length) return null
  // Distinct categorical palette so each race/ethnicity segment is easy to tell
  // apart (the old single-hue cobalt-opacity ramp blurred adjacent segments
  // together). These mid-tone hues read on both the cream light surface and the
  // dark-navy dark-mode surface; gold/amber is intentionally excluded (reserved
  // for "earned" beats per the design system).
  const PALETTE = ['#3b82f6', '#10b981', '#8b5cf6', '#ec4899', '#06b6d4', '#f43f5e']
  const shade = (i: number) => PALETTE[i] ?? '#94a3b8'
  const total = items.reduce((a, s) => a + s.pct, 0)
  const remainder = Math.max(0, 1 - total)
  return (
    <div data-testid="diversity-bar">
      <div
        className="flex h-3 w-full overflow-hidden rounded-full"
        role="img"
        aria-label="Race and ethnicity breakdown"
      >
        {items.map((s, i) => (
          <div
            key={s.label}
            style={{ width: `${s.pct * 100}%`, backgroundColor: shade(i) }}
            title={`${s.label} ${Math.round(s.pct * 100)}%`}
          />
        ))}
        {remainder > 0.001 && (
          <div
            style={{ width: `${remainder * 100}%`, backgroundColor: 'hsl(var(--muted))' }}
            title={`Other ${Math.round(remainder * 100)}%`}
          />
        )}
      </div>
      <div className="mt-2.5 flex flex-wrap gap-x-3 gap-y-1">
        {items.map((s, i) => (
          <span
            key={s.label}
            className="inline-flex items-center gap-1.5 text-[11.5px] text-muted-foreground"
          >
            <span
              className="h-2 w-2 rounded-sm"
              style={{ backgroundColor: shade(i) }}
              aria-hidden="true"
            />
            {s.label}{' '}
            <span className="font-semibold tabular-nums text-foreground">
              {Math.round(s.pct * 100)}%
            </span>
          </span>
        ))}
        {remainder > 0.001 && (
          <span className="inline-flex items-center gap-1.5 text-[11.5px] text-muted-foreground">
            <span
              className="h-2 w-2 rounded-sm border border-border"
              style={{ backgroundColor: 'hsl(var(--muted))' }}
              aria-hidden="true"
            />
            Other{' '}
            <span className="font-semibold tabular-nums text-foreground">
              {Math.round(remainder * 100)}%
            </span>
          </span>
        )}
      </div>
    </div>
  )
}

/** Small rounded tags (e.g. top industries). */
export function ChipList({ items }: { items: string[] }) {
  if (!items?.length) return null
  return (
    <div className="flex flex-wrap gap-1.5">
      {items.map(it => (
        <span
          key={it}
          className="rounded-full border border-border bg-muted/50 px-2.5 py-1 text-[12px] text-foreground/80"
        >
          {it}
        </span>
      ))}
    </div>
  )
}
