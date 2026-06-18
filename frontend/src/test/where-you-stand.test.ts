import { describe, expect, it } from 'vitest'

import { buildStandComparisons, cohortHasComparableMetric } from '../pages/student/program/standComparison'
import type { AcademicRecord, TestScore } from '../types'

function academic(partial: Partial<AcademicRecord>): AcademicRecord {
  return {
    id: 'a1',
    student_id: 's1',
    institution_name: 'State U',
    degree_type: 'bachelors',
    field_of_study: 'CS',
    gpa: null,
    gpa_scale: null,
    start_date: '2018-09-01',
    end_date: '2022-06-01',
    is_current: false,
    honors: null,
    thesis_title: null,
    country: null,
    transcript_language: null,
    credential_evaluation_status: null,
    credential_evaluation_report_url: null,
    rigor_indicator_count: null,
    courses: [],
    created_at: '',
    updated_at: '',
    ...partial,
  }
}

function score(partial: Partial<TestScore>): TestScore {
  return {
    id: 't1',
    student_id: 's1',
    test_type: 'GRE',
    total_score: null,
    section_scores: null,
    test_date: '2023-01-01',
    is_official: true,
    created_at: '',
    updated_at: '',
    ...partial,
  }
}

describe('buildStandComparisons', () => {
  it('returns nothing when there is no class profile', () => {
    expect(buildStandComparisons({ classProfile: null, academicRecords: [], testScores: [] })).toEqual([])
  })

  it('omits a metric when the student has no matching value', () => {
    const out = buildStandComparisons({
      classProfile: { median_gpa: 3.8 },
      academicRecords: [],
      testScores: [],
    })
    expect(out).toEqual([])
  })

  it('omits GPA when the cohort has no median', () => {
    const out = buildStandComparisons({
      classProfile: { cohort_size: 100 },
      academicRecords: [academic({ gpa: 3.7 })],
      testScores: [],
    })
    expect(out).toEqual([])
  })

  it('reads GPA above the cohort median', () => {
    const out = buildStandComparisons({
      classProfile: { median_gpa: 3.6 },
      academicRecords: [academic({ gpa: 3.8 })],
      testScores: [],
    })
    expect(out).toHaveLength(1)
    expect(out[0].label).toBe('GPA')
    expect(out[0].placement).toBe('above')
    expect(out[0].read).toBe("Your GPA (3.8) sits above this program's median (3.6).")
  })

  it('reads GPA below the cohort median', () => {
    const out = buildStandComparisons({
      classProfile: { median_gpa: 3.9 },
      academicRecords: [academic({ gpa: 3.5 })],
      testScores: [],
    })
    expect(out[0].placement).toBe('below')
    expect(out[0].read).toContain('below')
  })

  it('reads GPA exactly at the cohort median', () => {
    const out = buildStandComparisons({
      classProfile: { median_gpa: 3.7 },
      academicRecords: [academic({ gpa: 3.7 })],
      testScores: [],
    })
    expect(out[0].placement).toBe('at')
    expect(out[0].read).toContain('right at')
  })

  it('omits GPA when scales are not comparable', () => {
    const out = buildStandComparisons({
      classProfile: { median_gpa: 8.5, gpa_scale: 10 },
      academicRecords: [academic({ gpa: 3.8, gpa_scale: '4.0' })],
      testScores: [],
    })
    expect(out).toEqual([])
  })

  it('compares GPA when scales match', () => {
    const out = buildStandComparisons({
      classProfile: { median_gpa: 3.6, gpa_scale: 4 },
      academicRecords: [academic({ gpa: 3.9, gpa_scale: '4.0' })],
      testScores: [],
    })
    expect(out).toHaveLength(1)
    expect(out[0].scaleMax).toBe(4)
  })

  it('picks the most recent GPA record', () => {
    const out = buildStandComparisons({
      classProfile: { median_gpa: 3.5 },
      academicRecords: [
        academic({ id: 'old', gpa: 3.0, end_date: '2018-06-01' }),
        academic({ id: 'new', gpa: 3.9, end_date: '2023-06-01' }),
      ],
      testScores: [],
    })
    expect(out[0].yourValue).toBe(3.9)
  })

  it('reads GRE Quant from section_scores', () => {
    const out = buildStandComparisons({
      classProfile: { median_gre_quant: 165 },
      academicRecords: [],
      testScores: [score({ test_type: 'GRE', section_scores: { quant: 168 } })],
    })
    expect(out).toHaveLength(1)
    expect(out[0].label).toBe('GRE Quant')
    expect(out[0].placement).toBe('above')
    expect(out[0].scaleMax).toBe(170)
  })

  it('reads GMAT from total_score', () => {
    const out = buildStandComparisons({
      classProfile: { median_gmat: 720 },
      academicRecords: [],
      testScores: [score({ test_type: 'GMAT', total_score: 700 })],
    })
    expect(out).toHaveLength(1)
    expect(out[0].label).toBe('GMAT')
    expect(out[0].placement).toBe('below')
  })

  it('coerces a string cohort median like "3.92 (Class of 2024)"', () => {
    const out = buildStandComparisons({
      classProfile: { median_gpa: '3.92 (Class of 2024)' },
      academicRecords: [academic({ gpa: 3.95 })],
      testScores: [],
    })
    expect(out).toHaveLength(1)
    expect(out[0].cohortMedian).toBe(3.92)
    expect(out[0].cohortDisplay).toBe('3.92')
  })

  it('combines GPA + GMAT when both sides exist', () => {
    const out = buildStandComparisons({
      classProfile: { median_gpa: 3.6, median_gmat: 710 },
      academicRecords: [academic({ gpa: 3.7 })],
      testScores: [score({ test_type: 'GMAT', total_score: 730 })],
    })
    expect(out.map((c) => c.key).sort()).toEqual(['gmat', 'gpa'])
  })
})

describe('cohortHasComparableMetric', () => {
  it('is false for an empty or non-academic profile', () => {
    expect(cohortHasComparableMetric(null)).toBe(false)
    expect(cohortHasComparableMetric({ cohort_size: 100, women_pct: 0.5 })).toBe(false)
  })

  it('is true when any median anchor is present', () => {
    expect(cohortHasComparableMetric({ median_gpa: 3.8 })).toBe(true)
    expect(cohortHasComparableMetric({ median_gre_quant: 168 })).toBe(true)
    expect(cohortHasComparableMetric({ median_gmat: 720 })).toBe(true)
  })
})
