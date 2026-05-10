/**
 * Phase B PR 1 — Smoke test for the new Phase A API client modules.
 *
 * Doesn't make real HTTP requests; just verifies that every module imports
 * cleanly, every exported function has a callable signature, and every
 * shared type is importable from the types barrel. If a future change
 * removes or renames one of these contracts, this test breaks at type-check
 * time before anyone hits the runtime path.
 */
import { describe, expect, it } from 'vitest'

import * as discovery from '../api/discovery'
import * as goals from '../api/goals'
import * as identity from '../api/identity'
import * as needs from '../api/needs'
import * as strategy from '../api/strategy'
import * as workshopsFeedback from '../api/workshops-feedback'
import * as matching from '../api/matching'

import type {
  AppendMessageResponse,
  CompletionMap,
  CoreValue,
  DiscoveryMessage,
  DiscoverySession,
  ExplainMatchResponse,
  MatchResultDual,
  StudentGoal,
  StudentIdentity,
  StudentNeed,
  StudentStrategy,
  WorkshopFeedbackRun,
} from '../types'

describe('Phase A API client modules', () => {
  it('discovery exports the lifecycle + completion functions', () => {
    expect(typeof discovery.startSession).toBe('function')
    expect(typeof discovery.listSessions).toBe('function')
    expect(typeof discovery.getSession).toBe('function')
    expect(typeof discovery.updateSession).toBe('function')
    expect(typeof discovery.appendMessage).toBe('function')
    expect(typeof discovery.getCompletionMap).toBe('function')
  })

  it('goals exports CRUD', () => {
    expect(typeof goals.listGoals).toBe('function')
    expect(typeof goals.createGoal).toBe('function')
    expect(typeof goals.updateGoal).toBe('function')
    expect(typeof goals.deleteGoal).toBe('function')
  })

  it('needs exports CRUD', () => {
    expect(typeof needs.listNeeds).toBe('function')
    expect(typeof needs.createNeed).toBe('function')
    expect(typeof needs.updateNeed).toBe('function')
    expect(typeof needs.deleteNeed).toBe('function')
  })

  it('identity exports get/upsert/regenerate', () => {
    expect(typeof identity.getIdentity).toBe('function')
    expect(typeof identity.upsertIdentity).toBe('function')
    expect(typeof identity.regenerateIdentitySummary).toBe('function')
  })

  it('strategy exports the full lifecycle', () => {
    expect(typeof strategy.generateStrategy).toBe('function')
    expect(typeof strategy.getActiveStrategy).toBe('function')
    expect(typeof strategy.listStrategyVersions).toBe('function')
    expect(typeof strategy.getStrategy).toBe('function')
    expect(typeof strategy.activateStrategy).toBe('function')
    expect(typeof strategy.updateStrategy).toBe('function')
  })

  it('workshops-feedback exports all three domains + runs list', () => {
    expect(typeof workshopsFeedback.requestEssayFeedback).toBe('function')
    expect(typeof workshopsFeedback.requestInterviewPractice).toBe('function')
    expect(typeof workshopsFeedback.requestTestGuidance).toBe('function')
    expect(typeof workshopsFeedback.listWorkshopRuns).toBe('function')
  })

  it('matching exports the new explainMatch endpoint', () => {
    expect(typeof matching.explainMatch).toBe('function')
    expect(typeof matching.getMatchDetail).toBe('function')
  })
})

describe('Phase A type barrel', () => {
  it('compiles a representative shape from each new domain', () => {
    // The point of this test is the type assertions below — if any of the
    // shared types drift, this file fails to compile in CI.
    const session: DiscoverySession = {
      id: 'x',
      student_id: 'y',
      track: 'goals',
      layer: null,
      status: 'active',
      completion_pct: '0',
      exit_signal: null,
      started_at: '',
      completed_at: null,
      created_at: '',
      updated_at: '',
    }
    const msg: DiscoveryMessage = {
      id: 'a',
      session_id: 'b',
      role: 'student',
      content: 'hi',
      extracted_signals: null,
      created_at: '',
    }
    const append: AppendMessageResponse = {
      student_message: msg,
      assistant_message: null,
    }
    const completion: CompletionMap = {
      profile: '0',
      goals: '0',
      needs: '0',
      identity: '0',
    }
    const goal: StudentGoal = {
      id: 'g',
      student_id: 's',
      category: 'academic',
      specific: 'x',
      measurable: null,
      achievable_notes: null,
      relevant_notes: null,
      time_bound: null,
      status: 'active',
      source: 'manual',
      source_session_id: null,
      confidence: null,
      created_at: '',
      updated_at: '',
    }
    const need: StudentNeed = {
      id: 'n',
      student_id: 's',
      maslow_level: 'safety',
      need_type: 'healthcare',
      signal: 'x',
      severity: 'must_have',
      source: 'manual',
      source_session_id: null,
      source_quote: null,
      confidence: null,
      created_at: '',
      updated_at: '',
    }
    const value: CoreValue = {
      value: 'curiosity',
      evidence: 'x',
      confidence: null,
      source_quote: null,
    }
    const ident: StudentIdentity = {
      student_id: 's',
      core_values: [value],
      worldview: [],
      self_awareness: [],
      identity_summary: null,
      last_session_id: null,
      updated_at: '',
    }
    const strat: StudentStrategy = {
      id: 'st',
      student_id: 's',
      version: 1,
      status: 'draft',
      career_target: null,
      target_degree: null,
      academic_path: [],
      financial_path: [],
      geographic_path: [],
      narrative: null,
      generated_at: '',
      generated_from_session_ids: [],
      is_stub: true,
      created_at: '',
      updated_at: '',
    }
    const match: MatchResultDual = {
      id: 'm',
      student_id: 's',
      program_id: 'p',
      fitness_score: '0.85',
      confidence_score: '0.7',
      fitness_breakdown: null,
      confidence_breakdown: null,
      rationale_text: null,
      rationale_generated_at: null,
      strategy_version_id: null,
      match_score: null,
      score_breakdown: null,
      match_tier: null,
      reasoning_text: null,
      model_version: null,
      computed_at: '',
      is_stale: false,
    }
    const explain: ExplainMatchResponse = {
      program_id: 'p',
      rationale_text: 'x',
      rationale_generated_at: '',
      is_stub: true,
    }
    const run: WorkshopFeedbackRun = {
      id: 'r',
      student_id: 's',
      domain: 'essay',
      input_artifact_id: null,
      prompt_text: null,
      rubric_scores: {},
      structural_issues: [],
      missing_elements: [],
      suggested_questions: [],
      is_stub: true,
      created_at: '',
    }
    expect([session, msg, append, completion, goal, need, ident, strat, match, explain, run].length).toBe(11)
  })
})
