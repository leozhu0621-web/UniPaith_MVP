import type {
  SegmentRule,
  SegmentRuleGroup,
  SegmentRuleTree,
  SignalDef,
  SignalDictionary,
} from '../../../types'

/** A fresh, empty rule tree (include AND / exclude AND). */
export function emptyTree(): SegmentRuleTree {
  return { include: { op: 'AND', rules: [] }, exclude: { op: 'AND', rules: [] } }
}

/** Map of signal key → definition for quick lookup. */
export function indexSignals(dict: SignalDictionary | undefined): Record<string, SignalDef> {
  const map: Record<string, SignalDef> = {}
  for (const s of dict?.signals ?? []) map[s.key] = s
  return map
}

/** A sensible default rule for a freshly-picked signal. */
export function defaultRuleForSignal(
  sig: SignalDef,
  branch: 'include' | 'exclude' = 'include',
): SegmentRule {
  const operator = sig.operators[0] ?? 'in'
  let value: any
  if (operator === 'exists') value = undefined
  else if (sig.value_type === 'days') value = 30
  else if (sig.value_type === 'number') value = 50
  else value = [] // enum_multi / band / enum_single start empty
  return { field: sig.key, operator, value, branch }
}

const OP_LABEL: Record<string, string> = {
  gt: '≥',
  gte: '≥',
  lt: '≤',
  lte: '≤',
  between: 'between',
}

function valueToLabel(sig: SignalDef, value: any): string {
  if (Array.isArray(value)) {
    if (sig.options) {
      const m = Object.fromEntries(sig.options.map((o) => [o.value, o.label]))
      return value.map((v) => m[v] ?? v).join(', ')
    }
    return value.join(', ')
  }
  if (sig.options) {
    const m = Object.fromEntries(sig.options.map((o) => [o.value, o.label]))
    return m[String(value)] ?? String(value)
  }
  return String(value ?? '')
}

/** Render a leaf rule as a plain-language sentence (spec §4). */
export function renderRule(sig: SignalDef | undefined, rule: SegmentRule): string {
  if (!sig) return `${rule.field} ${rule.operator} ${rule.value ?? ''}`
  const rendered = valueToLabel(sig, rule.value)
  const opLabel = OP_LABEL[rule.operator] ?? rule.operator
  try {
    return sig.plain_language.replace('{value}', rendered).replace('{operator}', opLabel)
  } catch {
    return sig.plain_language
  }
}

/** The raw `field · operator · value` string shown on hover (spec §4). */
export function rawRuleString(rule: SegmentRule): string {
  const v = rule.value === undefined ? '✓' : JSON.stringify(rule.value)
  return `${rule.field} · ${rule.operator} · ${v}`
}

/** Is this rule fully specified (has a usable value)? */
export function ruleIsComplete(rule: SegmentRule): boolean {
  if (rule.operator === 'exists') return true
  if (Array.isArray(rule.value)) return rule.value.length > 0
  if (rule.operator === 'between') return Array.isArray(rule.value) && rule.value.length === 2
  return rule.value !== undefined && rule.value !== null && rule.value !== ''
}

/** Whether a tree has any rules at all. */
export function treeHasRules(tree: SegmentRuleTree): boolean {
  return tree.include.rules.length > 0 || tree.exclude.rules.length > 0
}

/** Flatten an NL-bridge flat rule list into include/exclude branches. */
export function rulesToTree(rules: SegmentRule[]): SegmentRuleTree {
  const tree = emptyTree()
  for (const r of rules) {
    const branch = r.branch === 'exclude' ? 'exclude' : 'include'
    tree[branch].rules.push({ ...r, branch })
  }
  return tree
}

/** Read a stored value back into a builder tree (handles legacy / partial shapes). */
export function normalizeStoredRules(rules: SegmentRuleTree | null | undefined): SegmentRuleTree {
  if (!rules) return emptyTree()
  const onlyLeaves = (
    group: SegmentRuleGroup | undefined,
    branch: 'include' | 'exclude',
  ): SegmentRuleGroup => {
    if (!group) return { op: 'AND', rules: [] }
    const leaves = (group.rules ?? [])
      .filter((r): r is SegmentRule => 'field' in r)
      .map((r) => ({ ...r, branch }))
    return { op: group.op === 'OR' ? 'OR' : 'AND', rules: leaves }
  }
  return {
    include: onlyLeaves(rules.include, 'include'),
    exclude: onlyLeaves(rules.exclude, 'exclude'),
  }
}

export const FIT_BAND_LABEL: Record<string, string> = {
  high: 'High',
  medium: 'Medium',
  low: 'Low',
}
