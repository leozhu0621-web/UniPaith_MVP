import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import Badge from '../../../../components/ui/Badge'
import Skeleton from '../../../../components/ui/Skeleton'
import QueryError from '../../../../components/ui/QueryError'
import { getOffersComparison } from '../../../../api/offers'
import type { OfferComparisonItem } from '../../../../types'
import {
  money,
  formatTermDate,
  DECISION_STATE_LABEL,
  daysUntil,
  deadlineTone,
  DEADLINE_TONE_CLASS,
} from './offerFormat'
import { Award, Sparkles, PiggyBank, ShieldCheck } from 'lucide-react'

const pct = (n: number | null | undefined) =>
  n == null ? '—' : `${Math.round(n * 100)}%`

/** One labelled row across all offer columns. */
function Row({
  label,
  offers,
  render,
  highlight,
}: {
  label: string
  offers: OfferComparisonItem[]
  render: (o: OfferComparisonItem) => React.ReactNode
  highlight?: (o: OfferComparisonItem) => boolean
}) {
  return (
    <tr className="border-t border-border">
      <th
        scope="row"
        className="text-left align-top py-2.5 pr-4 text-xs font-semibold uppercase tracking-wider text-foreground whitespace-nowrap"
      >
        {label}
      </th>
      {offers.map(o => (
        <td
          key={o.offer_id}
          className={`py-2.5 px-3 text-sm align-top ${
            highlight?.(o) ? 'text-foreground font-semibold' : 'text-foreground'
          }`}
        >
          {render(o)}
        </td>
      ))}
    </tr>
  )
}

/**
 * Side-by-side offer comparison table. Inform + view only — no respond
 * action lives here (that stays in OfferPanel). Rendered inline in the
 * Offers view and inside the DecisionComparison modal for its other callers.
 */
export default function OfferComparisonTable({
  enabled = true,
  onNavigate = () => {},
  className,
}: {
  /** Gate the fetch — the modal passes `isOpen` for a lazy-on-open fetch. */
  enabled?: boolean
  /** Called before navigating from a header button (the modal passes onClose). */
  onNavigate?: () => void
  className?: string
}) {
  const navigate = useNavigate()
  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['offers-comparison'],
    queryFn: getOffersComparison,
    enabled,
  })

  const offers = data?.offers ?? []
  const ind = data?.indicators
  const minNet = Math.min(
    ...offers.map(o => (o.cost.net_cost == null ? Infinity : o.cost.net_cost)),
  )
  const maxFit = Math.max(...offers.map(o => o.fit.fitness ?? -1))

  if (isLoading) return <Skeleton className={`h-64 ${className ?? ''}`} />

  if (isError)
    return (
      <QueryError
        title="We couldn't load your offers."
        detail="Your comparison didn't load just now."
        onRetry={() => refetch()}
      />
    )

  if (offers.length === 0)
    return (
      <p className="text-sm text-foreground py-6 text-center">
        No offers to compare yet. They'll appear here as decisions arrive.
      </p>
    )

  return (
    <div className={`space-y-4 ${className ?? ''}`}>
      {data?.advisor_summary && (
        <p className="text-sm text-foreground leading-relaxed rounded-lg bg-muted px-3 py-2.5">
          {data.advisor_summary}
        </p>
      )}
      <div className="overflow-x-auto">
        <table className="w-full border-collapse">
          <thead>
            <tr>
              <th className="w-32" />
              {offers.map(o => (
                <th key={o.offer_id} scope="col" className="text-left py-2 px-3 min-w-[180px]">
                  <button
                    type="button"
                    onClick={() => {
                      onNavigate()
                      navigate(`/s/applications/${o.application_id}?tab=offer`)
                    }}
                    className="text-left hover:opacity-80 transition-opacity"
                  >
                    <p className="text-sm font-semibold text-foreground leading-snug">
                      {o.program_name || 'Program'}
                    </p>
                    {o.institution_name && (
                      <p className="text-xs text-foreground">{o.institution_name}</p>
                    )}
                  </button>
                  <div className="flex flex-wrap gap-1 mt-1.5">
                    {ind?.most_affordable === o.application_id && (
                      <Badge variant="success">
                        <PiggyBank size={10} className="mr-0.5 inline" />
                        Most affordable
                      </Badge>
                    )}
                    {ind?.best_fit === o.application_id && (
                      <Badge variant="info">
                        <Sparkles size={10} className="mr-0.5 inline" />
                        Best fit
                      </Badge>
                    )}
                    {ind?.best_value === o.application_id && (
                      <Badge variant="warning">
                        <Award size={10} className="mr-0.5 inline" />
                        Best value
                      </Badge>
                    )}
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            <Row
              label="Decision"
              offers={offers}
              render={o => DECISION_STATE_LABEL[o.decision_state || 'pending'] || '—'}
            />
            <Row
              label="Net cost"
              offers={offers}
              highlight={o => o.cost.net_cost != null && o.cost.net_cost === minNet}
              render={o => money(o.cost.net_cost, o.cost.currency) ?? '—'}
            />
            <Row
              label="Tuition"
              offers={offers}
              render={o => money(o.cost.tuition, o.cost.currency) ?? '—'}
            />
            <Row
              label="Scholarship"
              offers={offers}
              render={o => money(o.cost.scholarship, o.cost.currency) ?? '—'}
            />
            <Row
              label="Fitness"
              offers={offers}
              highlight={o => o.fit.fitness != null && o.fit.fitness === maxFit}
              render={o => pct(o.fit.fitness)}
            />
            <Row label="Confidence" offers={offers} render={o => pct(o.fit.confidence)} />
            <Row
              label="Outcomes"
              offers={offers}
              render={o =>
                o.outcomes.median_salary
                  ? `${money(o.outcomes.median_salary)} median`
                  : '—'
              }
            />
            <Row label="Location" offers={offers} render={o => o.location || '—'} />
            <Row
              label="Respond by"
              offers={offers}
              highlight={o => {
                const d = daysUntil(o.response_deadline)
                return d != null && d >= 0 && d <= 7
              }}
              render={o => {
                const d = daysUntil(o.response_deadline)
                const tone = deadlineTone(d)
                const label = formatTermDate(o.response_deadline) || '—'
                return (
                  <span className={d != null && d >= 0 ? DEADLINE_TONE_CLASS[tone] : undefined}>
                    {label}
                    {d != null && d >= 0 && d <= 14 && tone !== 'normal' && (
                      <span className="block text-xs mt-0.5">{d}d left</span>
                    )}
                  </span>
                )
              }}
            />
            <Row
              label="Placement"
              offers={offers}
              render={o =>
                o.outcomes.placement_rate != null
                  ? `${Math.round(o.outcomes.placement_rate * 100)}%`
                  : '—'
              }
            />
            {/* No per-offer "must-haves met" verdict: the backend returns the
                student's must-haves as a flat list with NO per-offer satisfaction
                data, so a green "Likely met" inferred from the fitness score would
                fabricate a claim we can't substantiate (data-honesty rule). The
                honest "Your must-haves" list renders below instead. */}
          </tbody>
        </table>
      </div>

      {data?.must_have_constraints && data.must_have_constraints.length > 0 && (
        <div className="rounded-lg bg-muted p-3">
          <div className="flex items-center gap-1.5 mb-1.5">
            <ShieldCheck size={14} className="text-secondary" />
            <p className="text-xs font-semibold uppercase tracking-wider text-foreground">
              Your must-haves
            </p>
          </div>
          <ul className="text-sm text-foreground space-y-0.5">
            {data.must_have_constraints.map((c, i) => (
              <li key={i}>
                <span className="font-medium">{c.need}</span>
                {c.signal ? ` — ${c.signal}` : ''}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}
