import Card from '../../../components/ui/Card'
import Badge from '../../../components/ui/Badge'
import { formatPercent } from '../../../utils/format'
import type { CampaignAttributionData, EventAttributionData } from '../../../types'

interface AttributionPanelProps {
  campaigns: CampaignAttributionData[]
  events: EventAttributionData[]
}

export default function AttributionPanel({ campaigns, events }: AttributionPanelProps) {
  return (
    <div className="space-y-6">
      <Card className="p-5">
        <h3 className="text-sm font-semibold text-foreground mb-4">Campaign performance</h3>
        {campaigns.length === 0 ? (
          <p className="text-sm text-muted-foreground text-center py-8">No sent campaigns yet.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-muted-foreground border-b border-border">
                  <th className="py-2 pr-4">Campaign</th>
                  <th className="py-2 px-2 text-right">Sent</th>
                  <th className="py-2 px-2 text-right">Delivered</th>
                  <th className="py-2 px-2 text-right">Delivery rate</th>
                  <th className="py-2 px-2 text-right">Opened</th>
                  <th className="py-2 px-2 text-right">Clicked</th>
                  <th className="py-2 pl-2 text-right">Apps started</th>
                </tr>
              </thead>
              <tbody>
                {campaigns.map(c => (
                  <tr key={c.campaign_id} className="border-b border-border/50">
                    <td className="py-2 pr-4 font-medium text-foreground">{c.campaign_name}</td>
                    <td className="py-2 px-2 text-right tabular-nums">{c.recipients}</td>
                    <td className="py-2 px-2 text-right tabular-nums">{c.delivered}</td>
                    <td className="py-2 px-2 text-right tabular-nums">
                      {c.delivery_rate != null ? formatPercent(c.delivery_rate) : '—'}
                    </td>
                    <td className="py-2 px-2 text-right tabular-nums">{c.opened}</td>
                    <td className="py-2 px-2 text-right tabular-nums">{c.clicked}</td>
                    <td className="py-2 pl-2 text-right">
                      <Badge variant={c.applications_started > 0 ? 'success' : 'neutral'}>
                        {c.applications_started}
                      </Badge>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      <Card className="p-5">
        <h3 className="text-sm font-semibold text-foreground mb-4">Event performance</h3>
        {events.length === 0 ? (
          <p className="text-sm text-muted-foreground text-center py-8">No events yet.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-muted-foreground border-b border-border">
                  <th className="py-2 pr-4">Event</th>
                  <th className="py-2 px-2 text-right">RSVPs</th>
                  <th className="py-2 px-2 text-right">Attended</th>
                  <th className="py-2 pl-2 text-right">Apps after</th>
                </tr>
              </thead>
              <tbody>
                {events.map(e => (
                  <tr key={e.event_id} className="border-b border-border/50">
                    <td className="py-2 pr-4 font-medium text-foreground">{e.event_name}</td>
                    <td className="py-2 px-2 text-right tabular-nums">{e.rsvps}</td>
                    <td className="py-2 px-2 text-right tabular-nums">{e.attended}</td>
                    <td className="py-2 pl-2 text-right">
                      <Badge variant={e.applications_after > 0 ? 'success' : 'neutral'}>
                        {e.applications_after}
                      </Badge>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  )
}
