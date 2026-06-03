// Spec 62 — the shared evaluation-harness transparency types.
// Kept in their own module (build.ts carries a large duplicated legacy block);
// build.ts imports EvalHarnessSummary for BuildOverview, and the page/api import
// the rest from here.
import type { OpenQuestion, ReadinessStatus } from './build'

export interface EvalHarnessSummary {
  consumer_count: number
  consumers_live: number
  consumers_planned: number
  golden_case_total: number
  dimension_total: number
  hard_floor_dimension_count: number
  deterministic_check_total: number
  independent_judge_count: number
  judge_target_agreement: number
  suite_count: number
  suites_in_runner: number
  eval_mode_count: number
  modes_live: number
  new_table_count: number
  new_tables_present: number
  reused_table_count: number
  phase_count: number
  phases_live: number
  acceptance_count: number
  acceptance_live: number
  slo_count: number
  cost_control_count: number
  open_question_count: number
  backing_route_count: number
  config_knob_count: number
  provider: string
  live_is_source_of_truth: boolean
}

export interface EvalHarnessDimension {
  key: string
  label: string
  hard_floor: boolean
  kind: string // "deterministic" | "judge"
  summary: string
}

export interface EvalHarnessConsumerJudge {
  model: string
  independent: boolean
  system_under_test: string
  agreement: number | null
  target_agreement: number
  status: string
  note: string
}

export interface EvalHarnessConsumer {
  key: string
  title: string
  spec: string
  file: string | null
  status: ReadinessStatus
  golden_case_count: number
  golden_version: string | null
  hooks: {
    produce: string
    rubric: string
    materialize: string
    materialize_source: string
  }
  dimensions: EvalHarnessDimension[]
  deterministic_checks: { name: string; blurb: string }[]
  judge: EvalHarnessConsumerJudge | null
}

export interface EvalHarnessHook {
  hook: string
  blurb: string
}

export interface EvalHarnessMode {
  n: number
  key: string
  title: string
  blurb: string
  status: ReadinessStatus
  backing_table: string
  backing_table_present: boolean
}

export interface EvalHarnessSuite {
  key: string
  title: string
  hard_floor: boolean
  blurb: string
  in_runner: boolean
  threshold: Record<string, number>
}

export interface EvalHarnessTable {
  name: string
  blurb: string
  present: boolean
  column_count: number
}

export interface EvalHarnessStatusItem {
  status: ReadinessStatus
  text: string
}

export interface EvalHarnessSyntheticItem {
  key: string
  title: string
  status: ReadinessStatus
  blurb: string
}

export interface EvalHarnessPhase {
  key: string
  title: string
  blurb: string
  status: ReadinessStatus
}

export interface EvalHarnessConfigKnob {
  name: string
  value: string | number | boolean
  section: string
}

export interface EvalHarnessRoutes {
  chatbot: string[]
  extraction: string[]
}

export interface EvalHarness {
  the_bar: { statement: string; principle: string }
  summary: EvalHarnessSummary
  consumers: EvalHarnessConsumer[]
  adapter_hooks: EvalHarnessHook[]
  eval_modes: EvalHarnessMode[]
  suites: EvalHarnessSuite[]
  data_model: {
    new_tables: EvalHarnessTable[]
    reused_tables: EvalHarnessTable[]
  }
  synthetic_redteam: EvalHarnessSyntheticItem[]
  slos: EvalHarnessStatusItem[]
  cost_controls: EvalHarnessStatusItem[]
  phases: EvalHarnessPhase[]
  acceptance: EvalHarnessStatusItem[]
  open_questions: OpenQuestion[]
  config_knobs: EvalHarnessConfigKnob[]
  routes: EvalHarnessRoutes
  tiers: Record<string, string>
}
