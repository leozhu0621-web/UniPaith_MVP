import Card from '../../../components/ui/Card'
import type { TopSource } from '../../../types'

interface TopContentPanelProps {
  byClicks: TopSource[]
  byApplyStarted: TopSource[]
}

function SourceList({ title, items }: { title: string; items: TopSource[] }) {
  return (
    <Card className="p-5">
      <h3 className="text-sm font-semibold text-foreground mb-3">{title}</h3>
      {items.length === 0 ? (
        <p className="text-sm text-muted-foreground py-6 text-center">No ranked content yet.</p>
      ) : (
        <ol className="space-y-2">
          {items.map((s, i) => (
            <li key={`${s.source_kind}-${s.source_id}`} className="flex items-center gap-3 text-sm">
              <span className="w-5 text-muted-foreground tabular-nums">{i + 1}.</span>
              <div className="flex-1 min-w-0">
                <p className="font-medium text-foreground truncate">{s.source_name}</p>
                <p className="text-xs text-muted-foreground capitalize">{s.source_kind.replace('_', ' ')}</p>
              </div>
              <span className="font-semibold tabular-nums text-foreground">{s.action_count}</span>
            </li>
          ))}
        </ol>
      )}
    </Card>
  )
}

export default function TopContentPanel({ byClicks, byApplyStarted }: TopContentPanelProps) {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
      <SourceList title="By clicks" items={byClicks} />
      <SourceList title="By apply started" items={byApplyStarted} />
    </div>
  )
}
