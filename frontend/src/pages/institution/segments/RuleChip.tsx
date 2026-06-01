import { useState } from 'react'
import { X, HelpCircle, AlertTriangle } from 'lucide-react'
import type { SegmentRule, SignalDef } from '../../../types'
import { renderRule, rawRuleString, ruleIsComplete } from './helpers'

interface Props {
  signal: SignalDef | undefined
  rule: SegmentRule
  editable?: boolean
  onChange?: (next: SegmentRule) => void
  onRemove?: () => void
}

/** Spec 26 §4 / 02 §9 — a rule rendered as a plain-language constraint chip
 *  (cobalt outline). Hover reveals the raw field·operator·value; clicking the
 *  label opens an in-place editor. An ambiguous rule (from AI assist) gets a `?`. */
export default function RuleChip({ signal, rule, editable = false, onChange, onRemove }: Props) {
  const [editing, setEditing] = useState(false)
  const incomplete = !ruleIsComplete(rule)

  return (
    <span className="relative inline-flex">
      <span
        title={rawRuleString(rule)}
        className={[
          'inline-flex items-center gap-1.5 rounded-full border bg-surface pl-3 pr-2 py-1 text-sm',
          incomplete ? 'border-warning text-warning' : 'border-cobalt text-foreground',
        ].join(' ')}
      >
        {rule.ambiguous && (
          <HelpCircle size={13} className="text-warning" aria-label="AI inferred — review" />
        )}
        {incomplete && (
          <AlertTriangle size={12} className="text-warning" aria-label="Needs a value" />
        )}
        <button
          type="button"
          disabled={!editable}
          onClick={() => editable && setEditing((v) => !v)}
          className={
            editable
              ? 'hover:underline underline-offset-2 cursor-pointer text-left'
              : 'cursor-default'
          }
        >
          {renderRule(signal, rule)}
        </button>
        {onRemove && (
          <button
            type="button"
            onClick={onRemove}
            aria-label="Remove rule"
            className="ml-0.5 rounded-full p-0.5 text-muted-foreground hover:bg-muted hover:text-foreground"
          >
            <X size={13} />
          </button>
        )}
      </span>

      {editing && signal && onChange && (
        <>
          <div className="fixed inset-0 z-10" onClick={() => setEditing(false)} aria-hidden />
          <RuleEditor
            signal={signal}
            rule={rule}
            onChange={(r) => onChange(r)}
            onClose={() => setEditing(false)}
          />
        </>
      )}
    </span>
  )
}

function RuleEditor({
  signal,
  rule,
  onChange,
  onClose,
}: {
  signal: SignalDef
  rule: SegmentRule
  onChange: (r: SegmentRule) => void
  onClose: () => void
}) {
  const set = (patch: Partial<SegmentRule>) => onChange({ ...rule, ...patch, ambiguous: false })

  const toggleMulti = (v: string) => {
    const cur: string[] = Array.isArray(rule.value) ? rule.value : []
    set({ value: cur.includes(v) ? cur.filter((x) => x !== v) : [...cur, v] })
  }

  return (
    <div className="absolute top-full left-0 z-20 mt-1 w-72 rounded-lg border border-border bg-surface p-3 shadow-lg">
      <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
        {signal.label}
      </p>
      {signal.help_text && <p className="mb-2 text-xs text-muted-foreground">{signal.help_text}</p>}

      {/* Operator (only when >1 choice) */}
      {signal.operators.length > 1 && (
        <div className="mb-2 flex flex-wrap gap-1">
          {signal.operators.map((op) => (
            <button
              key={op}
              type="button"
              onClick={() => set({ operator: op })}
              className={[
                'rounded-md border px-2 py-0.5 text-xs',
                rule.operator === op
                  ? 'border-cobalt bg-cobalt/10 text-cobalt'
                  : 'border-border text-muted-foreground',
              ].join(' ')}
            >
              {op === 'gt' ? '≥' : op === 'lt' ? '≤' : op}
            </button>
          ))}
        </div>
      )}

      {/* Value editor by type */}
      {(signal.value_type === 'enum_multi' ||
        signal.value_type === 'band' ||
        signal.value_type === 'enum_single') &&
        signal.options && (
          <div className="flex flex-col gap-1.5">
            {signal.options.map((o) => {
              const checked = Array.isArray(rule.value) && rule.value.includes(o.value)
              return (
                <label key={o.value} className="flex cursor-pointer items-center gap-2 text-sm">
                  <input
                    type="checkbox"
                    checked={checked}
                    onChange={() => toggleMulti(o.value)}
                    className="rounded border-border text-cobalt focus:ring-cobalt"
                  />
                  <span>{o.label}</span>
                </label>
              )
            })}
          </div>
        )}

      {(signal.value_type === 'enum_multi' || signal.value_type === 'enum_single') &&
        !signal.options && (
          <input
            type="text"
            value={Array.isArray(rule.value) ? rule.value.join(', ') : ''}
            onChange={(e) =>
              set({
                value: e.target.value
                  ? e.target.value
                      .split(',')
                      .map((s) => s.trim())
                      .filter(Boolean)
                  : [],
              })
            }
            placeholder="e.g. computer science, data"
            className="w-full rounded-md border-border text-sm focus:border-cobalt focus:ring-cobalt"
          />
        )}

      {signal.value_type === 'days' && (
        <div className="flex items-center gap-2 text-sm">
          <input
            type="number"
            min={1}
            value={typeof rule.value === 'number' ? rule.value : 30}
            onChange={(e) => set({ value: Number(e.target.value) || 30 })}
            className="w-24 rounded-md border-border text-sm focus:border-cobalt focus:ring-cobalt"
          />
          <span className="text-muted-foreground">days</span>
        </div>
      )}

      {signal.value_type === 'number' && rule.operator !== 'between' && (
        <input
          type="number"
          min={0}
          max={100}
          value={typeof rule.value === 'number' ? rule.value : 50}
          onChange={(e) => set({ value: Number(e.target.value) })}
          className="w-24 rounded-md border-border text-sm focus:border-cobalt focus:ring-cobalt"
        />
      )}

      {signal.value_type === 'number' && rule.operator === 'between' && (
        <div className="flex items-center gap-2 text-sm">
          <input
            type="number"
            value={Array.isArray(rule.value) ? (rule.value[0] ?? '') : ''}
            onChange={(e) =>
              set({
                value: [
                  Number(e.target.value),
                  Array.isArray(rule.value) ? (rule.value[1] ?? 100) : 100,
                ],
              })
            }
            className="w-20 rounded-md border-border text-sm focus:border-cobalt focus:ring-cobalt"
          />
          <span className="text-muted-foreground">to</span>
          <input
            type="number"
            value={Array.isArray(rule.value) ? (rule.value[1] ?? '') : ''}
            onChange={(e) =>
              set({
                value: [
                  Array.isArray(rule.value) ? (rule.value[0] ?? 0) : 0,
                  Number(e.target.value),
                ],
              })
            }
            className="w-20 rounded-md border-border text-sm focus:border-cobalt focus:ring-cobalt"
          />
        </div>
      )}

      {signal.value_type === 'boolean' && (
        <p className="text-sm text-muted-foreground">
          No value needed — presence of this signal is the rule.
        </p>
      )}

      <div className="mt-3 flex justify-end">
        <button
          type="button"
          onClick={onClose}
          className="rounded-md bg-secondary px-3 py-1 text-xs font-medium text-secondary-foreground hover:brightness-110"
        >
          Done
        </button>
      </div>
    </div>
  )
}
