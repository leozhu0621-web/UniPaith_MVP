/** Spec 26 — audience segmentation rule tree helpers. */

export type SegmentOperator =
  | 'equals'
  | 'in'
  | 'gt'
  | 'lt'
  | 'between'
  | 'within_days'
  | 'contains'
  | 'has_band'

export interface SegmentRule {
  field: string
  operator: SegmentOperator
  value: unknown
  ambiguous?: boolean
}

export interface SegmentRuleTree {
  op: 'AND' | 'OR' | 'NOT'
  rules: Array<SegmentRule | SegmentRuleTree>
}

export interface SegmentCriteriaPayload {
  description?: string
  frequency_cap_per_week?: number | null
  uploaded_list_ids?: string[]
  include?: SegmentRuleTree
  exclude?: SegmentRuleTree
  /** Legacy flat keys — kept for backward compatibility with resolver */
  statuses?: string[]
  decisions?: string[]
  min_match_score?: number | null
  max_match_score?: number | null
  match_tiers?: number[]
  min_engagement_signals?: number | null
  engagement_types?: string[]
  nationalities?: string[]
  has_applied?: boolean | null
  applied_after?: string
}

export interface RuleFieldDef {
  field: string
  category: string
  label: string
  operators: SegmentOperator[]
  valueType: 'number' | 'string' | 'string_list' | 'band' | 'days' | 'boolean'
  defaultOperator: SegmentOperator
  defaultValue: unknown
  options?: { value: string; label: string }[]
}

export const RULE_FIELD_CATALOG: RuleFieldDef[] = [
  {
    field: 'engagement.viewed_institution',
    category: 'Activity',
    label: 'Viewed institution page',
    operators: ['within_days'],
    valueType: 'days',
    defaultOperator: 'within_days',
    defaultValue: 30,
  },
  {
    field: 'engagement.saved_program',
    category: 'Activity',
    label: 'Saved a program',
    operators: ['within_days'],
    valueType: 'days',
    defaultOperator: 'within_days',
    defaultValue: 90,
  },
  {
    field: 'engagement.compared_program',
    category: 'Activity',
    label: 'Compared programs',
    operators: ['within_days'],
    valueType: 'days',
    defaultOperator: 'within_days',
    defaultValue: 90,
  },
  {
    field: 'engagement.requested_info',
    category: 'Activity',
    label: 'Requested info',
    operators: ['within_days'],
    valueType: 'days',
    defaultOperator: 'within_days',
    defaultValue: 90,
  },
  {
    field: 'engagement.event_rsvp',
    category: 'Activity',
    label: 'RSVP’d to an event',
    operators: ['within_days'],
    valueType: 'days',
    defaultOperator: 'within_days',
    defaultValue: 180,
  },
  {
    field: 'application.started',
    category: 'Activity',
    label: 'Started application',
    operators: ['equals'],
    valueType: 'boolean',
    defaultOperator: 'equals',
    defaultValue: true,
  },
  {
    field: 'application.not_submitted',
    category: 'Activity',
    label: 'Started but not submitted',
    operators: ['equals'],
    valueType: 'boolean',
    defaultOperator: 'equals',
    defaultValue: true,
  },
  {
    field: 'fit.fitness_band',
    category: 'Fit',
    label: 'Fit band',
    operators: ['has_band'],
    valueType: 'band',
    defaultOperator: 'has_band',
    defaultValue: 'high',
    options: [
      { value: 'high', label: 'High' },
      { value: 'medium', label: 'Medium' },
      { value: 'low', label: 'Low' },
    ],
  },
  {
    field: 'match.tier',
    category: 'Fit',
    label: 'Match tier',
    operators: ['in'],
    valueType: 'string_list',
    defaultOperator: 'in',
    defaultValue: ['target'],
    options: [
      { value: 'reach', label: 'Reach' },
      { value: 'target', label: 'Target' },
      { value: 'safer', label: 'Safer' },
    ],
  },
  {
    field: 'readiness.budget_band',
    category: 'Readiness',
    label: 'Budget sensitivity',
    operators: ['has_band'],
    valueType: 'band',
    defaultOperator: 'has_band',
    defaultValue: 'high',
    options: [
      { value: 'high', label: 'High sensitivity' },
      { value: 'medium', label: 'Medium' },
      { value: 'low', label: 'Low sensitivity' },
    ],
  },
  {
    field: 'readiness.modality',
    category: 'Readiness',
    label: 'Modality preference',
    operators: ['in'],
    valueType: 'string_list',
    defaultOperator: 'in',
    defaultValue: ['online'],
    options: [
      { value: 'in_person', label: 'In person' },
      { value: 'online', label: 'Online' },
      { value: 'hybrid', label: 'Hybrid' },
    ],
  },
  {
    field: 'readiness.timeline',
    category: 'Readiness',
    label: 'Timeline urgency',
    operators: ['equals'],
    valueType: 'string',
    defaultOperator: 'equals',
    defaultValue: 'this_intake',
    options: [
      { value: 'this_intake', label: 'This intake' },
      { value: 'next_intake', label: 'Next intake' },
      { value: 'later', label: 'Later' },
    ],
  },
  {
    field: 'suppression.unsubscribed',
    category: 'Exclude',
    label: 'Unsubscribed from outreach',
    operators: ['equals'],
    valueType: 'boolean',
    defaultOperator: 'equals',
    defaultValue: true,
  },
  {
    field: 'application.status',
    category: 'Pipeline',
    label: 'Application status',
    operators: ['in'],
    valueType: 'string_list',
    defaultOperator: 'in',
    defaultValue: ['submitted'],
    options: [
      { value: 'submitted', label: 'Submitted' },
      { value: 'under_review', label: 'Under review' },
      { value: 'interview', label: 'Interview' },
      { value: 'decision_made', label: 'Decision made' },
    ],
  },
  {
    field: 'profile.nationality',
    category: 'Profile',
    label: 'Nationality',
    operators: ['in'],
    valueType: 'string_list',
    defaultOperator: 'in',
    defaultValue: [],
  },
]

export const EXCLUDE_PRESETS: RuleFieldDef[] = [
  RULE_FIELD_CATALOG.find(f => f.field === 'application.started')!,
  RULE_FIELD_CATALOG.find(f => f.field === 'suppression.unsubscribed')!,
]

export function fieldDef(field: string): RuleFieldDef | undefined {
  return RULE_FIELD_CATALOG.find(f => f.field === field)
}

export function isRuleTree(node: SegmentRule | SegmentRuleTree): node is SegmentRuleTree {
  return 'op' in node && Array.isArray((node as SegmentRuleTree).rules)
}

export function plainLanguageRule(rule: SegmentRule): string {
  const def = fieldDef(rule.field)
  const base = def?.label ?? rule.field.replace(/\./g, ' ')
  const v = rule.value

  switch (rule.operator) {
    case 'within_days':
      return `${base} in the last ${v} days`
    case 'has_band':
      return `${base} ≥ ${formatValue(v)}`
    case 'in':
      return `${base}: ${formatList(v)}`
    case 'equals':
      if (typeof v === 'boolean') return v ? base : `Not: ${base}`
      return `${base} is ${formatValue(v)}`
    case 'gt':
      return `${base} > ${formatValue(v)}`
    case 'lt':
      return `${base} < ${formatValue(v)}`
    case 'between':
      return `${base} between ${formatList(v)}`
    case 'contains':
      return `${base} contains ${formatValue(v)}`
    default:
      return base
  }
}

export function rawRuleTooltip(rule: SegmentRule): string {
  return `${rule.field} · ${rule.operator} · ${JSON.stringify(rule.value)}`
}

function formatValue(v: unknown): string {
  if (v == null) return '—'
  if (typeof v === 'string') return v.replace(/_/g, ' ')
  return String(v)
}

function formatList(v: unknown): string {
  if (Array.isArray(v)) return v.map(formatValue).join(', ')
  return formatValue(v)
}

export function flattenRules(tree: SegmentRuleTree | undefined): SegmentRule[] {
  if (!tree?.rules?.length) return []
  const out: SegmentRule[] = []
  for (const node of tree.rules) {
    if (isRuleTree(node)) out.push(...flattenRules(node))
    else out.push(node)
  }
  return out
}

export function defaultIncludeTree(): SegmentRuleTree {
  return { op: 'AND', rules: [] }
}

export function defaultExcludeTree(): SegmentRuleTree {
  return { op: 'OR', rules: [] }
}

export function criteriaToPayload(c: SegmentCriteriaPayload): Record<string, unknown> {
  const out: Record<string, unknown> = {}
  if (c.description?.trim()) out.description = c.description.trim()
  if (c.frequency_cap_per_week != null) out.frequency_cap_per_week = c.frequency_cap_per_week
  if (c.uploaded_list_ids?.length) out.uploaded_list_ids = c.uploaded_list_ids
  if (c.include?.rules?.length) out.include = c.include
  if (c.exclude?.rules?.length) out.exclude = c.exclude
  if (c.statuses?.length) out.statuses = c.statuses
  if (c.decisions?.length) out.decisions = c.decisions
  if (c.min_match_score != null) out.min_match_score = c.min_match_score
  if (c.max_match_score != null) out.max_match_score = c.max_match_score
  if (c.match_tiers?.length) out.match_tiers = c.match_tiers
  if (c.min_engagement_signals != null) out.min_engagement_signals = c.min_engagement_signals
  if (c.engagement_types?.length) out.engagement_types = c.engagement_types
  if (c.nationalities?.length) out.nationalities = c.nationalities
  if (c.has_applied != null) out.has_applied = c.has_applied
  if (c.applied_after) out.applied_after = c.applied_after
  return out
}

export function payloadToCriteria(obj: Record<string, unknown> | null | undefined): SegmentCriteriaPayload {
  const c = obj ?? {}
  return {
    description: typeof c.description === 'string' ? c.description : '',
    frequency_cap_per_week: typeof c.frequency_cap_per_week === 'number' ? c.frequency_cap_per_week : null,
    uploaded_list_ids: Array.isArray(c.uploaded_list_ids) ? (c.uploaded_list_ids as string[]) : [],
    include: parseTree(c.include) ?? defaultIncludeTree(),
    exclude: parseTree(c.exclude) ?? defaultExcludeTree(),
    statuses: Array.isArray(c.statuses) ? (c.statuses as string[]) : [],
    decisions: Array.isArray(c.decisions) ? (c.decisions as string[]) : [],
    min_match_score: typeof c.min_match_score === 'number' ? c.min_match_score : null,
    max_match_score: typeof c.max_match_score === 'number' ? c.max_match_score : null,
    match_tiers: Array.isArray(c.match_tiers) ? (c.match_tiers as number[]) : [],
    min_engagement_signals: typeof c.min_engagement_signals === 'number' ? c.min_engagement_signals : null,
    engagement_types: Array.isArray(c.engagement_types) ? (c.engagement_types as string[]) : [],
    nationalities: Array.isArray(c.nationalities) ? (c.nationalities as string[]) : [],
    has_applied: typeof c.has_applied === 'boolean' ? c.has_applied : null,
    applied_after: typeof c.applied_after === 'string' ? c.applied_after : '',
  }
}

function parseTree(raw: unknown): SegmentRuleTree | null {
  if (!raw || typeof raw !== 'object') return null
  const t = raw as SegmentRuleTree
  if (!t.op || !Array.isArray(t.rules)) return null
  return t
}

export function newRuleFromField(fieldKey: string): SegmentRule {
  const def = fieldDef(fieldKey)
  if (!def) {
    return { field: fieldKey, operator: 'equals', value: true }
  }
  return {
    field: def.field,
    operator: def.defaultOperator,
    value: def.defaultValue,
  }
}
