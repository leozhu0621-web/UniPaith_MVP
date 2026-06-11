/**
 * Spec 23 ↔ Spec 11 data-contract tests.
 *
 * Proves the institution editor's canonical blobs (Spec 23 §3) both
 *   (a) project onto the legacy shape the student page renders (programNormalize)
 *   (b) survive a hydrate → serialize round-trip in the editor (helpers).
 * Also guards the percent → fraction scale conversion the student page depends on.
 */
import { describe, expect, it } from 'vitest'
import {
  normalizeCostData,
  normalizeOutcomes,
  normalizeRequirements,
  intakeDeadlineFromArray,
  intakeTimelineFromArray,
  extractTracksMeta,
  extractPrerequisites,
  extractTestPolicy,
  extractRecommendations,
  extractFundingSignals,
  extractSalaryBands,
} from '../utils/programNormalize'
import { fromProgram, toPayload, emptyDraft } from '../pages/institution/program-editor/helpers'
import type { Program } from '../types'

describe('normalizeCostData', () => {
  it('projects canonical cost_data onto legacy keys', () => {
    const cd = normalizeCostData({
      tuition_amount: 48000,
      tuition_currency: 'USD',
      tuition_period: 'per_year',
      fees: [
        { name: 'Lab fee', amount: 300, required: true },
        { name: 'Activity fee', amount: 120, required: false },
      ],
      estimated_total_cost_band: { min: 80000, max: 92000, currency: 'USD' },
    })
    expect(cd.tuition_annual).toBe(48000)
    expect(cd.fees).toEqual({ 'Lab fee': 300, 'Activity fee': 120 })
    expect(cd.total_cost_attendance).toBe(92000)
  })

  it('passes legacy cost_data through untouched', () => {
    const cd = normalizeCostData({
      tuition_annual: 50000,
      fees: { health: 400 },
      total_cost_attendance: 80000,
      source: 'College Scorecard',
    })
    expect(cd.tuition_annual).toBe(50000)
    expect(cd.fees).toEqual({ health: 400 })
    expect(cd.total_cost_attendance).toBe(80000)
    expect(cd.source).toBe('College Scorecard') // legacy extras preserved
  })
})

describe('normalizeOutcomes', () => {
  it('converts canonical percents to the 0–1 fractions the page renders ×100', () => {
    const od = normalizeOutcomes({
      median_starting_salary: 95000,
      placement_rate_pct: 94,
      internship_to_offer_pct: 80,
      top_employers: ['Google', 'Microsoft'],
      common_roles: ['Software Engineer'],
      outcome_reporting_window: 'Within 6 months (Class of 2024)',
    })
    expect(od.median_salary).toBe(95000)
    expect(od.employment_rate).toBeCloseTo(0.94)
    expect(od.internship_conversion_rate).toBeCloseTo(0.8)
    expect(od.top_employers).toEqual(['Google', 'Microsoft'])
    expect(od.top_industries).toEqual(['Software Engineer']) // common_roles fallback
    // a leading "Within " is stripped so the page's "Within {tf}" never doubles
    expect(od.employment_timeframe).toBe('6 months (Class of 2024)')
  })

  it('passes legacy fraction outcomes through', () => {
    const od = normalizeOutcomes({ median_salary: 80000, employment_rate: 0.9 })
    expect(od.median_salary).toBe(80000)
    expect(od.employment_rate).toBe(0.9)
  })
})

describe('normalizeRequirements', () => {
  it('flattens canonical materials to the checklist shape', () => {
    const reqs = normalizeRequirements({
      materials: [
        { name: 'Statement of purpose', required: true, note: '500 words' },
        { name: 'Portfolio', required: false },
      ],
      prerequisites: [],
    })
    expect(reqs).toEqual([
      { label: 'Statement of purpose', required: true, note: '500 words' },
      { label: 'Portfolio', required: false, note: undefined },
    ])
  })

  it('passes a legacy array checklist through', () => {
    const reqs = normalizeRequirements([{ label: 'Transcript', required: true }])
    expect(reqs[0].label).toBe('Transcript')
  })

  it('returns [] for empty/unknown shapes', () => {
    expect(normalizeRequirements(null)).toEqual([])
    expect(normalizeRequirements([])).toEqual([])
  })
})

describe('intake rounds (array shape)', () => {
  it('picks the earliest deadline', () => {
    expect(
      intakeDeadlineFromArray([{ deadline: '2027-01-05' }, { deadline: '2026-11-01' }]),
    ).toBe('2026-11-01')
  })

  it('builds a render-ready timeline', () => {
    const tl = intakeTimelineFromArray([
      {
        name: 'Round 1',
        term: { season: 'Fall', year: 2027 },
        deadline: '2026-11-01',
        decision_date: '2027-01-15',
      },
      { name: 'No deadline yet', term: { season: 'Fall', year: 2027 }, deadline: null },
    ])
    expect(tl?.term).toBe('Fall 2027')
    expect(tl?.rounds).toHaveLength(1) // the deadline-less round is dropped
    expect(tl?.rounds[0]).toMatchObject({
      name: 'Round 1',
      deadline: '2026-11-01',
      decision_release: '2027-01-15',
    })
  })
})

describe('extractStructuredFields', () => {
  const appReqs = {
    materials: [{ name: 'Essay', required: true }],
    prerequisites: [{ name: 'Calculus I–III', required: true, allowed_substitutes: ['AP Calc BC'] }],
    test_policy: {
      stance: 'test_optional',
      required: ['GRE'],
      optional: ['GMAT'],
      accepted_tests: ['GRE', 'GMAT'],
      superscore_enabled: true,
      waived_rules: 'Waived with 5+ years experience',
      typical_ranges: [{ test: 'GRE', low: 310, high: 330 }],
    },
    recommendations: { required_count: 2, types: ['academic', 'professional'] },
  }

  it('extracts tracks metadata from canonical tracks object', () => {
    const meta = extractTracksMeta({ concentrations: ['AI', 'Systems'], note: 'Pick one', learning_format: 'Cohort-based' })
    expect(meta.concentrations).toEqual(['AI', 'Systems'])
    expect(meta.note).toBe('Pick one')
    expect(meta.learning_format).toBe('Cohort-based')
  })

  it('extracts tracks from the data-module items shape ({name} objects)', () => {
    const meta = extractTracksMeta({
      label: 'MBA certificates',
      note: 'Seven optional certificates',
      items: [{ name: 'Finance Certificate' }, { name: 'Healthcare Certificate' }],
    })
    expect(meta.concentrations).toEqual(['Finance Certificate', 'Healthcare Certificate'])
    expect(meta.note).toBe('Seven optional certificates')
  })

  it('extracts prerequisites, test policy, and recommendations', () => {
    expect(extractPrerequisites(appReqs)).toHaveLength(1)
    const tp = extractTestPolicy(appReqs)
    expect(tp?.stance_label).toBe('Test-optional')
    expect(tp?.optional).toEqual(['GMAT'])
    expect(tp?.typical_ranges[0]).toEqual({ test: 'GRE', low: 310, high: 330 })
    expect(extractRecommendations(appReqs)).toEqual({ required_count: 2, types: ['academic', 'professional'] })
  })

  it('extracts funding signals and salary bands', () => {
    const fs = extractFundingSignals({
      funding_signals: { ta_funded: true, ra_funded: false, merit_scholarship_available: true, need_based_available: false },
    })
    expect(fs?.ta_funded).toBe(true)
    expect(extractSalaryBands({
      salary_distribution_bands: [{ band_label: '$80k–$100k', percent: 40 }, { band_label: '$100k+', percent: 35 }],
    })).toHaveLength(2)
  })
})

describe('editor hydrate → serialize round-trip', () => {
  const program: Program = {
    id: 'p1',
    institution_id: 'i1',
    program_name: 'Computer Science, M.S.',
    degree_type: 'masters',
    department: 'Engineering',
    duration_months: 24,
    tuition: 48000,
    acceptance_rate: 0.12,
    delivery_format: 'in_person',
    campus_setting: 'urban',
    requirements: { min_gpa: '3.0' },
    application_requirements: {
      materials: [{ name: 'Essay', required: true }],
      prerequisites: [],
      test_policy: {
        stance: 'test_optional',
        required: [],
        optional: [],
        accepted_tests: ['GRE'],
        superscore_enabled: true,
        waived_rules: '',
        typical_ranges: [],
      },
      recommendations: { required_count: 2, types: ['academic'] },
    },
    description_text: 'A rigorous program.',
    who_its_for: 'Builders.',
    is_published: false,
    application_deadline: '2027-01-05',
    program_start_date: null,
    tracks: { concentrations: ['AI', 'Systems'], note: 'Pick one' },
    outcomes_data: { median_starting_salary: 95000, placement_rate_pct: 94 },
    intake_rounds: [
      { id: 'r1', name: 'Round 1', term: { season: 'Fall', year: 2027 }, open_date: null, deadline: '2026-11-01', decision_date: null, start_date: null, capacity: 30 },
    ],
    media_urls: [],
    highlights: ['STEM-designated'],
    faculty_contacts: [],
    cost_data: {
      tuition_amount: 48000,
      tuition_currency: 'USD',
      tuition_period: 'per_year',
      fees: [{ name: 'Lab fee', amount: 300, required: true }],
      estimated_total_cost_band: { min: 80000, max: 92000, currency: 'USD' },
      funding_signals: { ta_funded: true, ra_funded: false, merit_scholarship_available: true, need_based_available: false },
    },
    promotion_categories: ['featured_discovery'],
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
  }

  it('preserves canonical fields through hydrate → serialize', () => {
    const payload = toPayload(fromProgram(program))
    expect(payload.program_name).toBe('Computer Science, M.S.')
    expect(payload.degree_type).toBe('masters')
    expect(payload.cost_data.tuition_amount).toBe(48000)
    expect(payload.cost_data.fees).toEqual([{ name: 'Lab fee', amount: 300, required: true }])
    expect(payload.cost_data.funding_signals.ta_funded).toBe(true)
    expect(payload.outcomes_data.median_starting_salary).toBe(95000)
    expect(payload.outcomes_data.placement_rate_pct).toBe(94)
    expect(payload.application_requirements.materials).toEqual([{ name: 'Essay', required: true, note: undefined }])
    expect(payload.application_requirements.test_policy.superscore_enabled).toBe(true)
    expect(payload.intake_rounds[0]).toMatchObject({ name: 'Round 1', deadline: '2026-11-01', capacity: 30 })
    expect(payload.promotion_categories).toEqual(['featured_discovery'])
    // tracks dict carries concentrations; acceptance rate decimal restored
    expect(payload.tracks).toMatchObject({ concentrations: ['AI', 'Systems'], note: 'Pick one' })
    expect(payload.acceptance_rate).toBeCloseTo(0.12)
  })

  it('syncs the top-level tuition column from cost_data for per-year tuition', () => {
    const payload = toPayload(fromProgram(program))
    expect(payload.tuition).toBe(48000)
  })

  it('hydrates a legacy program (array app-reqs, dict intake) without throwing', () => {
    const legacy: Program = {
      ...program,
      application_requirements: [{ label: 'Common App', required: true }] as any,
      intake_rounds: { fall_2027: { regular_decision: { deadline: '2027-01-05' } } } as any,
      cost_data: { tuition_annual: 50000, fees: { health: 400 } } as any,
      outcomes_data: { median_salary: 80000, employment_rate: 0.9 } as any,
    }
    const draft = fromProgram(legacy)
    expect(draft.application_requirements.materials[0].name).toBe('Common App')
    expect(draft.intake_rounds[0].deadline).toBe('2027-01-05')
    expect(draft.cost_data.tuition_amount).toBe(50000)
    expect(draft.outcomes_data.median_starting_salary).toBe(80000)
  })

  it('emptyDraft serializes to a minimal valid payload', () => {
    const payload = toPayload({ ...emptyDraft(), program_name: 'X', degree_type: 'masters' })
    expect(payload.program_name).toBe('X')
    expect(payload.cost_data.tuition_amount).toBeNull()
    expect(payload.intake_rounds).toEqual([])
  })
})
