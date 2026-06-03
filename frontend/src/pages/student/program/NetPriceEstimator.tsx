/**
 * Net Price Estimator — Spec 11 §3.3a.
 *
 * A personalized net-price range (not sticker) for this student at this program,
 * with a gap analysis against their stated budget. Editorial / brand-compliant:
 * cobalt is the only data-viz color, affordability uses the brand status tokens,
 * no gradients. Honesty: always a range, always the "estimate, not a quote" frame.
 *
 * Renders nothing when the estimate is unavailable (program lacks cost data) or
 * still loading — the caller's generic cost cards remain the fallback.
 */
import { Wallet, Info } from 'lucide-react'
import Card from '../../../components/ui/Card'
import Badge from '../../../components/ui/Badge'
import { formatCurrency } from '../../../utils/format'
import type { NetPriceEstimate, AffordabilityBand, AidLikelihoodBand } from '../../../types'

const BAND_META: Record<
  AffordabilityBand,
  { label: string; variant: 'success' | 'warning' | 'error' | 'neutral' } | null
> = {
  affordable: { label: 'Within your budget', variant: 'success' },
  stretch: { label: 'A stretch', variant: 'warning' },
  out_of_reach: { label: 'Over your budget', variant: 'error' },
  unknown: null,
}

const AID_LEVEL: Record<AidLikelihoodBand, number> = { low: 1, moderate: 2, high: 3, unknown: 0 }

interface Props {
  estimate?: NetPriceEstimate | null
  /** Sidebar echo — a single line instead of the full block. */
  compact?: boolean
}

export default function NetPriceEstimator({ estimate, compact = false }: Props) {
  if (!estimate || !estimate.available || !estimate.net_cost_scenario_range) return null

  const range = estimate.net_cost_scenario_range
  const coa = estimate.cost_of_attendance_annual ?? range.max
  const band = BAND_META[estimate.affordability_band]
  const aidLevel = AID_LEVEL[estimate.aid_scholarship_likelihood_band]

  // ── Compact (sidebar) ──
  if (compact) {
    return (
      <div className="rounded-lg border border-border bg-card p-3">
        <div className="flex items-center gap-1.5 mb-1">
          <Wallet size={13} className="text-secondary" />
          <p className="text-[11px] font-semibold uppercase tracking-wide text-foreground">
            Est. net price
          </p>
        </div>
        <p className="text-base font-bold text-foreground tabular-nums">
          ≈ {formatCurrency(range.expected)}
          <span className="text-[11px] font-normal text-foreground">/yr</span>
        </p>
        <p className="text-[10px] text-foreground/70 mt-0.5">
          {formatCurrency(range.min)}–{formatCurrency(range.max)} · estimate
        </p>
        {band && (
          <div className="mt-1.5">
            <Badge variant={band.variant} size="sm">{band.label}</Badge>
          </div>
        )}
      </div>
    )
  }

  // Range bar positions as a fraction of the sticker COA.
  const pct = (v: number) => `${Math.max(0, Math.min(100, (v / coa) * 100))}%`
  const minPct = pct(range.min)
  const widthPct = `${Math.max(2, Math.min(100, ((range.max - range.min) / coa) * 100))}%`
  const expectedPct = pct(range.expected)

  return (
    <Card className="p-5 border-secondary/30">
      <div className="flex items-center justify-between gap-2 mb-1">
        <div className="flex items-center gap-2">
          <Wallet size={15} className="text-secondary" />
          <h3 className="font-semibold text-foreground">Your estimated net price</h3>
        </div>
        <Badge variant="info" size="sm">Estimate, not a quote</Badge>
      </div>
      <p className="text-xs text-foreground mb-4">
        What you might actually pay per year after estimated grants &amp; scholarships — personalized
        to your profile, not the sticker price.
      </p>

      {/* Headline range */}
      <div className="flex items-end gap-2 mb-1">
        <p className="text-[28px] leading-none font-bold text-foreground tabular-nums">
          ≈ {formatCurrency(range.expected)}
        </p>
        <p className="text-sm text-foreground mb-0.5">/ year (expected)</p>
      </div>
      <p className="text-xs text-foreground mb-4">
        Likely range <span className="font-semibold text-foreground">{formatCurrency(range.min)}</span> –{' '}
        <span className="font-semibold text-foreground">{formatCurrency(range.max)}</span> per year
      </p>

      {/* Range bar — cobalt band within the neutral COA track, marker at expected */}
      <div className="mb-1">
        <div className="relative h-3 rounded-pill bg-muted overflow-hidden">
          <div
            className="absolute top-0 h-full rounded-pill bg-secondary/30"
            style={{ left: minPct, width: widthPct }}
          />
          <div
            className="absolute top-0 h-full w-[3px] rounded-pill bg-secondary"
            style={{ left: expectedPct }}
          />
        </div>
        <div className="flex justify-between mt-1 text-[10px] text-foreground/70">
          <span>$0</span>
          <span>Sticker {formatCurrency(coa)}/yr</span>
        </div>
      </div>

      {/* Gap analysis */}
      {band ? (
        <div className="flex items-center gap-2 mt-4 mb-3">
          <Badge variant={band.variant} size="md">{band.label}</Badge>
          <p className="text-xs text-foreground">
            {estimate.affordability_band === 'affordable'
              ? `Within your ${formatCurrency(estimate.gap.student_annual_budget)}/yr budget.`
              : `About ${formatCurrency(estimate.gap.shortfall_annual)}/yr over your ${formatCurrency(
                  estimate.gap.student_annual_budget,
                )}/yr budget.`}
          </p>
        </div>
      ) : (
        <p className="text-xs text-foreground mt-4 mb-3">
          Add a budget in your profile to see how this fits.
        </p>
      )}

      {/* Aid likelihood */}
      {aidLevel > 0 && (
        <div className="flex items-center gap-2 mb-3">
          <span className="text-xs text-foreground">Scholarship / aid likelihood</span>
          <span className="flex items-center gap-1" aria-hidden>
            {[1, 2, 3].map(i => (
              <span
                key={i}
                className={`w-2 h-2 rounded-full ${i <= aidLevel ? 'bg-secondary' : 'bg-muted'}`}
              />
            ))}
          </span>
          <span className="text-xs font-semibold text-foreground capitalize">
            {estimate.aid_scholarship_likelihood_band}
          </span>
        </div>
      )}

      {/* Drivers — what drives this estimate */}
      {estimate.drivers.length > 0 && (
        <ul className="space-y-1.5 mb-3">
          {estimate.drivers.map((d, i) => (
            <li key={i} className="flex items-start gap-2 text-xs text-foreground">
              <span className="w-1 h-1 rounded-full bg-secondary mt-1.5 flex-shrink-0" />
              {d}
            </li>
          ))}
        </ul>
      )}

      {/* Total over duration */}
      {estimate.net_cost_scenario_range_total && estimate.years && (
        <div className="rounded-lg bg-muted px-3 py-2 mb-3">
          <p className="text-xs text-foreground">
            Over {estimate.years} years:{' '}
            <span className="font-semibold text-foreground">
              ≈ {formatCurrency(estimate.net_cost_scenario_range_total.expected)}
            </span>{' '}
            ({formatCurrency(estimate.net_cost_scenario_range_total.min)}–
            {formatCurrency(estimate.net_cost_scenario_range_total.max)})
          </p>
        </div>
      )}

      {/* Honesty disclaimer */}
      <div className="flex items-start gap-1.5 text-[10px] text-foreground/60 border-t border-border pt-2">
        <Info size={11} className="flex-shrink-0 mt-0.5" />
        <span>{estimate.disclaimer}</span>
      </div>
    </Card>
  )
}
