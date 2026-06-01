import { useState } from 'react'
import { ChevronDown, ChevronUp, HelpCircle } from 'lucide-react'
import ConstraintChip from '../../../components/ui/ConstraintChip'
import Button from '../../../components/ui/Button'
import Select from '../../../components/ui/Select'
import Textarea from '../../../components/ui/Textarea'
import {
  RULE_FIELD_CATALOG,
  fieldDef,
  plainLanguageRule,
  rawRuleTooltip,
  newRuleFromField,
  type SegmentRule,
  type SegmentRuleTree,
} from './segmentRules'

interface SegmentRuleEditorProps {
  include: SegmentRuleTree
  exclude: SegmentRuleTree
  onIncludeChange: (tree: SegmentRuleTree) => void
  onExcludeChange: (tree: SegmentRuleTree) => void
  rawJson: string
  onRawJsonChange: (v: string) => void
  onApplyRawJson: () => void
}

function RuleList({
  branch,
  tree,
  onChange,
  addLabel,
}: {
  branch: 'Include' | 'Exclude'
  tree: SegmentRuleTree
  onChange: (tree: SegmentRuleTree) => void
  addLabel: string
}) {
  const rules = tree.rules.filter((r): r is SegmentRule => !('op' in r))

  const removeAt = (idx: number) => {
    onChange({ ...tree, rules: rules.filter((_, i) => i !== idx) })
  }

  const addField = (fieldKey: string) => {
    if (!fieldKey) return
    onChange({ ...tree, rules: [...rules, newRuleFromField(fieldKey)] })
  }

  const fieldOptions = [
    { value: '', label: addLabel },
    ...RULE_FIELD_CATALOG.filter(f => branch === 'Exclude' ? f.category === 'Exclude' || f.field.startsWith('application.') : f.category !== 'Exclude').map(
      f => ({ value: f.field, label: `${f.category} · ${f.label}` })
    ),
  ]

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <span className="text-sm font-semibold text-foreground">{branch}</span>
        <span className="text-xs text-muted-foreground uppercase tracking-wide">{tree.op}</span>
      </div>
      <div className="flex flex-wrap gap-2 min-h-[2rem]">
        {rules.length === 0 ? (
          <span className="text-sm text-muted-foreground">No rules yet</span>
        ) : (
          rules.map((rule, idx) => (
            <span key={`${rule.field}-${idx}`} className="inline-flex items-center gap-1" title={rawRuleTooltip(rule)}>
              <ConstraintChip
                category={fieldDef(rule.field)?.category ?? 'Rule'}
                value={plainLanguageRule(rule)}
                onRemove={() => removeAt(idx)}
              />
              {rule.ambiguous && (
                <span title="AI flagged this as ambiguous" className="inline-flex items-center text-warning">
                  <HelpCircle size={14} />
                </span>
              )}
            </span>
          ))
        )}
      </div>
      <Select
        label=""
        options={fieldOptions}
        value=""
        onChange={e => addField(e.target.value)}
      />
    </div>
  )
}

export default function SegmentRuleEditor({
  include,
  exclude,
  onIncludeChange,
  onExcludeChange,
  rawJson,
  onRawJsonChange,
  onApplyRawJson,
}: SegmentRuleEditorProps) {
  const [showAdvanced, setShowAdvanced] = useState(false)

  return (
    <div className="space-y-4 border border-border rounded-lg p-4 bg-muted/30">
      <RuleList branch="Include" tree={include} onChange={onIncludeChange} addLabel="Add include rule…" />
      <div className="border-t border-border pt-4">
        <RuleList branch="Exclude" tree={exclude} onChange={onExcludeChange} addLabel="Add exclude rule…" />
      </div>
      <div className="border-t border-border pt-3">
        {!showAdvanced ? (
          <button
            type="button"
            onClick={() => setShowAdvanced(true)}
            className="flex items-center gap-1 text-sm text-secondary hover:underline"
          >
            <ChevronDown size={14} /> Advanced (raw rule editor)
          </button>
        ) : (
          <div className="space-y-2">
            <button
              type="button"
              onClick={() => setShowAdvanced(false)}
              className="flex items-center gap-1 text-sm text-secondary hover:underline"
            >
              <ChevronUp size={14} /> Hide raw editor
            </button>
            <Textarea label="" value={rawJson} onChange={e => onRawJsonChange(e.target.value)} rows={8} />
            <Button size="sm" variant="ghost" onClick={onApplyRawJson}>Apply JSON</Button>
          </div>
        )}
      </div>
    </div>
  )
}
