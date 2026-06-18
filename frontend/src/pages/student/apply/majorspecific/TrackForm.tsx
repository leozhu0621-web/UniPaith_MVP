// Spec 43 — catalog-driven track form. Renders a track's groups → fields from
// the catalog schema (so all 15 tracks share one renderer), holds local edits,
// and saves the whole signal subdocument. Dirty state is derived by comparing to
// the persisted signals, so a successful save (which refetches) clears it
// automatically.
import { useState } from 'react'
import { Check } from 'lucide-react'

import Button from '../../../../components/ui/Button'
import Card from '../../../../components/ui/Card'
import type { TrackSchema, TrackSignals, TrackSignalValue } from '../../../../types/majorSpecific'

import TrackField from './fields'

function normalize(signals: TrackSignals): string {
  const clean: Record<string, TrackSignalValue> = {}
  for (const k of Object.keys(signals).sort()) {
    const v = signals[k]
    if (v === undefined || v === '' || (Array.isArray(v) && v.length === 0)) continue
    clean[k] = v
  }
  return JSON.stringify(clean)
}

export default function TrackForm({
  schema,
  initialSignals,
  onSave,
  saving,
}: {
  schema: TrackSchema
  initialSignals: TrackSignals
  onSave: (signals: TrackSignals) => void
  saving: boolean
}) {
  const [signals, setSignals] = useState<TrackSignals>(initialSignals)
  const dirty = normalize(signals) !== normalize(initialSignals)

  const setField = (key: string, value: TrackSignalValue | undefined) => {
    setSignals(prev => {
      const next = { ...prev }
      if (value === undefined) delete next[key]
      else next[key] = value
      return next
    })
  }

  return (
    <div className="space-y-4">
      {schema.groups.map(group => (
        <Card pad={false} key={group.key} variant="card-flush" className="space-y-1 p-4">
          <h4 className="mb-1 text-eyebrow uppercase tracking-wide text-muted-foreground">
            {group.label}
          </h4>
          <div className="divide-y divide-border/60">
            {group.fields.map(field => (
              <TrackField
                key={field.key}
                field={field}
                value={signals[field.key]}
                onChange={v => setField(field.key, v)}
              />
            ))}
          </div>
        </Card>
      ))}

      {/* Sticky save bar — cobalt CTA (gold is reserved for the readiness beat). */}
      <div className="sticky bottom-0 -mx-1 flex items-center justify-end gap-3 border-t border-border bg-background/95 px-1 py-3 backdrop-blur">
        {!dirty && !saving && (
          <span className="flex items-center gap-1 text-xs text-muted-foreground">
            <Check size={14} className="text-success" /> Saved
          </span>
        )}
        <Button
          variant="secondary"
          size="sm"
          disabled={!dirty || saving}
          loading={saving}
          onClick={() => onSave(signals)}
        >
          Save readiness
        </Button>
      </div>
    </div>
  )
}
