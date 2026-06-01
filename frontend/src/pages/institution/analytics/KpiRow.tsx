import Card from '../../../components/ui/Card'
import type { AnalyticsKpi } from '../../../types'
import { formatPercentSigned } from '../../../utils/format'

interface KpiRowProps {
  kpis: AnalyticsKpi[]
}

export default function KpiRow({ kpis }: KpiRowProps) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-3">
      {kpis.map(kpi => (
        <Card key={kpi.key} className="p-5">
          <p className="up-eyebrow">{kpi.label}</p>
          <p className="up-stat text-foreground mt-2">{kpi.value}</p>
          {kpi.comparison_pct != null && kpi.comparison_label ? (
            <p className="text-sm text-muted-foreground mt-1">
              {formatPercentSigned(kpi.comparison_pct)} {kpi.comparison_label}
            </p>
          ) : null}
        </Card>
      ))}
    </div>
  )
}
