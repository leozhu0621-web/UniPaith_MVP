import { useQuery } from '@tanstack/react-query'
import Modal from '../../../../components/ui/Modal'
import Badge from '../../../../components/ui/Badge'
import Skeleton from '../../../../components/ui/Skeleton'
import { getOffersComparison } from '../../../../api/offers'
import type { OfferComparisonItem } from '../../../../types'
import { money, formatTermDate, DECISION_STATE_LABEL } from './offerFormat'
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
    <tr className="border-t border-divider">
      <th
        scope="row"
        className="text-left align-top py-2.5 pr-4 text-xs font-semibold uppercase tracking-wider text-student-text whitespace-nowrap"
      >
        {label}
      </th>
      {offers.map(o => (
        <td
          key={o.offer_id}
          className={`py-2.5 px-3 text-sm align-top ${
            highlight?.(o) ? 'text-student-ink font-semibold' : 'text-student-ink'
          }`}
        >
          {render(o)}
        </td>
      ))}
    </tr>
  )
}

export default function DecisionComparison({
  isOpen,
  onClose,
}: {
  isOpen: boolean
  onClose: () => void
}) {
  const { data, isLoading } = useQuery({
    queryKey: ['offers-comparison'],
    queryFn: getOffersComparison,
    enabled: isOpen,
  })

  const offers = data?.offers ?? []
  const ind = data?.indicators
  const minNet = Math.min(
    ...offers.map(o => (o.cost.net_cost == null ? Infinity : o.cost.net_cost)),
  )
  const maxFit = Math.max(...offers.map(o => o.fit.fitness ?? -1))

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Compare your offers" size="lg">
      {isLoading ? (
        <Skeleton className="h-64" />
      ) : offers.length === 0 ? (
        <p className="text-sm text-student-text py-6 text-center">
          No offers to compare yet. They'll appear here as decisions arrive.
        </p>
      ) : (
        <div className="space-y-4">
          <div className="overflow-x-auto">
            <table className="w-full border-collapse">
              <thead>
                <tr>
                  <th className="w-32" />
                  {offers.map(o => (
                    <th key={o.offer_id} scope="col" className="text-left py-2 px-3 min-w-[180px]">
                      <p className="text-sm font-semibold text-student-ink leading-snug">
                        {o.program_name || 'Program'}
                      </p>
                      {o.institution_name && (
                        <p className="text-xs text-student-text">{o.institution_name}</p>
                      )}
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
                  render={o => formatTermDate(o.response_deadline) || '—'}
                />
              </tbody>
            </table>
          </div>

          {data?.must_have_constraints && data.must_have_constraints.length > 0 && (
            <div className="rounded-lg bg-student-mist p-3">
              <div className="flex items-center gap-1.5 mb-1.5">
                <ShieldCheck size={14} className="text-cobalt" />
                <p className="text-xs font-semibold uppercase tracking-wider text-student-text">
                  Your must-haves
                </p>
              </div>
              <ul className="text-sm text-student-ink space-y-0.5">
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
      )}
    </Modal>
  )
}
