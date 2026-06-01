import { Bar, BarChart, CartesianGrid, Cell, LabelList, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import type { FunnelStageItem } from '../../../types'
import { AXIS_TICK, CHART, GRID_STROKE, SERIES, TOOLTIP_STYLE } from './constants'

interface Props {
  stages: FunnelStageItem[]
  /** When true, color each stage from the brand series; else a single cobalt. */
  multicolor?: boolean
  height?: number
}

/**
 * Spec 28 §4 / §12 (G-I2) — the funnel rendered with recharts (replacing the
 * hand-rolled CSS bars). Horizontal bars by stage count, with conversion-to-prev
 * surfaced as a badge row beneath.
 */
export default function FunnelBars({ stages, multicolor = false, height }: Props) {
  const data = stages.map(s => ({ ...s }))
  const chartHeight = height ?? Math.max(180, stages.length * 46)

  return (
    <div>
      <ResponsiveContainer width="100%" height={chartHeight}>
        <BarChart layout="vertical" data={data} margin={{ top: 4, right: 44, left: 8, bottom: 0 }}>
          <CartesianGrid stroke={GRID_STROKE} strokeOpacity={0.5} horizontal={false} />
          <XAxis type="number" tick={AXIS_TICK} axisLine={false} tickLine={false} allowDecimals={false} />
          <YAxis
            type="category"
            dataKey="label"
            width={116}
            tick={{ fontSize: 12, fill: 'hsl(var(--foreground))' }}
            axisLine={false}
            tickLine={false}
          />
          <Tooltip contentStyle={TOOLTIP_STYLE} cursor={{ fill: 'hsl(var(--muted))', opacity: 0.4 }} />
          <Bar dataKey="count" radius={[0, 4, 4, 0]} maxBarSize={26}>
            {data.map((_, i) => (
              <Cell key={i} fill={multicolor ? SERIES[i % SERIES.length] : CHART.cobalt} />
            ))}
            <LabelList
              dataKey="count"
              position="right"
              style={{ fontSize: 12, fill: 'hsl(var(--foreground))', fontWeight: 700 }}
            />
          </Bar>
        </BarChart>
      </ResponsiveContainer>

      {stages.length > 1 && (
        <div className="mt-3 flex flex-wrap gap-x-4 gap-y-1.5">
          {stages.slice(1).map(s => (
            <span key={s.stage} className="text-xs text-muted-foreground tabular-nums">
              <span className="text-foreground">{s.label}</span>{' '}
              {s.conversion_from_prev == null ? '—' : `${Math.round(s.conversion_from_prev * 100)}% conv.`}
            </span>
          ))}
        </div>
      )}
    </div>
  )
}
