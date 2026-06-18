import type { SegmentRule, SegmentRuleGroup, SignalDef, SignalDictionary } from '../../../types'
import RuleChip from './RuleChip'
import SignalPicker from './SignalPicker'
import { defaultRuleForSignal } from './helpers'

interface Props {
  title: string
  hint?: string
  branch: 'include' | 'exclude'
  group: SegmentRuleGroup
  signals: Record<string, SignalDef>
  dict: SignalDictionary | undefined
  onChange: (group: SegmentRuleGroup) => void
}

/** Spec 26 §3 — one include/exclude branch: an AND/OR toggle + a row of
 *  editable plain-language rule chips + "Add rule". */
export default function RuleBranch({ title, hint, branch, group, signals, dict, onChange }: Props) {
  const leaves = group.rules.filter((r): r is SegmentRule => 'field' in r)

  const setRule = (idx: number, next: SegmentRule) => {
    const rules = [...group.rules]
    rules[idx] = next
    onChange({ ...group, rules })
  }
  const removeRule = (idx: number) => {
    const rules = group.rules.filter((_, i) => i !== idx)
    onChange({ ...group, rules })
  }
  const addRule = (sig: SignalDef) => {
    onChange({ ...group, rules: [...group.rules, defaultRuleForSignal(sig, branch)] })
  }

  return (
    <div className="rounded-lg border border-border bg-muted/30 p-4">
      <div className="mb-2 flex items-center justify-between">
        <div>
          <h4 className="text-sm font-semibold text-foreground">{title}</h4>
          {hint && <p className="text-xs text-muted-foreground">{hint}</p>}
        </div>
        {leaves.length > 1 && (
          <div className="flex items-center gap-1 text-xs">
            <span className="text-muted-foreground">Match</span>
            {(['AND', 'OR'] as const).map((op) => (
              <button
                key={op}
                type="button"
                onClick={() => onChange({ ...group, op })}
                className={[
                  'rounded-md border px-2 py-0.5 font-medium',
                  group.op === op
                    ? 'border-secondary bg-secondary/10 text-secondary'
                    : 'border-border text-muted-foreground',
                ].join(' ')}
              >
                {op === 'AND' ? 'all' : 'any'}
              </button>
            ))}
          </div>
        )}
      </div>

      <div className="flex flex-wrap items-center gap-2">
        {leaves.map((rule, idx) => (
          <div key={idx} className="flex items-center gap-2">
            {idx > 0 && (
              <span className="text-[11px] font-semibold uppercase text-muted-foreground">
                {group.op === 'OR' ? 'or' : 'and'}
              </span>
            )}
            <RuleChip
              signal={signals[rule.field]}
              rule={rule}
              editable
              onChange={(r) => setRule(group.rules.indexOf(rule), r)}
              onRemove={() => removeRule(group.rules.indexOf(rule))}
            />
          </div>
        ))}
        <SignalPicker dict={dict} onPick={addRule} label={leaves.length ? 'Add' : 'Add rule'} />
      </div>
    </div>
  )
}
