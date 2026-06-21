/**
 * whereYouStand — turns inert cohort numbers into self-relevant signal.
 *
 * A program's `class_profile` carries *median* anchors (median GPA, median GRE
 * Quant, median GMAT) — single points, not 25/75 ranges. So every comparison is
 * an honest placement relative to that median: at it, above it, or below it. We
 * never claim a "middle 50%" band the data doesn't contain, and we never invent
 * a number. A comparison renders only when BOTH the cohort anchor AND the
 * student's matching value exist.
 *
 * Tone is informational, never a verdict (see docs/UX-QA.md): we state where the
 * value sits, we don't grade the applicant.
 */

import type { AcademicRecord, TestScore } from '../../../types'

export interface StandComparison {
  /** Stable key for React lists. */
  key: string
  /** Short metric label, e.g. "GPA", "GRE Quant", "GMAT". */
  label: string
  /** The student's own value. */
  yourValue: number
  /** Display string for the student's value (preserves e.g. one decimal). */
  yourDisplay: string
  /** The cohort median anchor. */
  cohortMedian: number
  /** Display string for the cohort median. */
  cohortDisplay: string
  /** Bar scale max so the fill is meaningful (GPA → scale; tests → headroom). */
  scaleMax: number
  /** Where the student sits relative to the median. */
  placement: 'above' | 'at' | 'below'
  /** One-line, neutral read of the placement. */
  read: string
}

/** Coerce a possibly-string cohort value (some profiles store "424 students")
 *  to the leading number, or null if there's nothing numeric to read. */
function toNumber(raw: unknown): number | null {
  if (raw == null) return null
  if (typeof raw === 'number') return Number.isFinite(raw) ? raw : null
  if (typeof raw === 'string') {
    const m = raw.match(/-?\d+(\.\d+)?/)
    if (!m) return null
    const n = parseFloat(m[0])
    return Number.isFinite(n) ? n : null
  }
  return null
}

/** Trim a trailing ".0" so 3.80 reads as "3.8" but 320 stays "320". */
function trimDisplay(n: number): string {
  return Number.isInteger(n) ? String(n) : String(parseFloat(n.toFixed(2)))
}

/** Pick the student's representative GPA: the most recent completed record with
 *  a GPA, else any record with one. We do not average across scales. */
function pickStudentGpa(records: AcademicRecord[] | undefined): { value: number; scale: number | null } | null {
  if (!records || records.length === 0) return null
  const withGpa = records.filter((r) => r.gpa != null && Number.isFinite(Number(r.gpa)))
  if (withGpa.length === 0) return null
  // Prefer the latest by end_date (completed), falling back to start order.
  const sorted = [...withGpa].sort((a, b) => {
    const ad = a.end_date ?? a.start_date ?? ''
    const bd = b.end_date ?? b.start_date ?? ''
    return bd.localeCompare(ad)
  })
  const r = sorted[0]
  const scale = r.gpa_scale ? toNumber(r.gpa_scale) : null
  return { value: Number(r.gpa), scale }
}

/** Pull a score for one test type from the student's test scores (latest first).
 *  `section` lets us read GRE Quant out of section_scores. */
function pickTestScore(
  scores: TestScore[] | undefined,
  testType: TestScore['test_type'],
  section?: string,
): number | null {
  if (!scores || scores.length === 0) return null
  const matches = scores
    .filter((s) => s.test_type === testType)
    .sort((a, b) => (b.test_date ?? '').localeCompare(a.test_date ?? ''))
  for (const s of matches) {
    if (section) {
      const v = s.section_scores?.[section]
      if (v != null && Number.isFinite(Number(v))) return Number(v)
    } else if (s.total_score != null && Number.isFinite(Number(s.total_score))) {
      return Number(s.total_score)
    }
  }
  return null
}

function placementOf(yourValue: number, median: number): StandComparison['placement'] {
  const diff = yourValue - median
  // A hair off the median reads as "at" — avoid implying precision the medians
  // don't have. GPA tolerance is tighter than test-score tolerance.
  if (Math.abs(diff) < 1e-9) return 'at'
  return diff > 0 ? 'above' : 'below'
}

function readLine(label: string, yourDisplay: string, cohortDisplay: string, placement: StandComparison['placement']): string {
  const where =
    placement === 'above'
      ? `above this program's median (${cohortDisplay})`
      : placement === 'below'
        ? `below this program's median (${cohortDisplay})`
        : `right at this program's median (${cohortDisplay})`
  return `Your ${label} (${yourDisplay}) sits ${where}.`
}

interface BuildInput {
  classProfile: Record<string, unknown> | null | undefined
  academicRecords: AcademicRecord[] | undefined
  testScores: TestScore[] | undefined
}

/**
 * Build the list of comparisons to render. Only metrics where BOTH the cohort
 * median and the student's value exist are returned; everything else is omitted
 * silently. Never fabricates a number or a range.
 */
export function buildStandComparisons({ classProfile, academicRecords, testScores }: BuildInput): StandComparison[] {
  const cp = classProfile && typeof classProfile === 'object' ? classProfile : null
  if (!cp) return []

  const out: StandComparison[] = []

  // ── GPA ──
  const cohortGpa = toNumber(cp.median_gpa)
  if (cohortGpa != null) {
    const studentGpa = pickStudentGpa(academicRecords)
    if (studentGpa != null) {
      // Only compare when scales are comparable. If the student's scale is known
      // and differs from the cohort's stated gpa_scale, we omit rather than
      // compare a 4.0 against a 10.0 and mislead.
      const cohortScale = toNumber(cp.gpa_scale)
      const scalesComparable =
        studentGpa.scale == null || cohortScale == null || Math.abs(studentGpa.scale - cohortScale) < 1e-9
      if (scalesComparable) {
        // First POSITIVE scale wins — a 0/negative scale (?? only catches null)
        // would zero scaleMax and divide-by-zero the bar fill.
        const scaleMax = [studentGpa.scale, cohortScale].find(s => s != null && s > 0) ?? 4.0
        const placement = placementOf(studentGpa.value, cohortGpa)
        const yourDisplay = trimDisplay(studentGpa.value)
        const cohortDisplay = trimDisplay(cohortGpa)
        out.push({
          key: 'gpa',
          label: 'GPA',
          yourValue: studentGpa.value,
          yourDisplay,
          cohortMedian: cohortGpa,
          cohortDisplay,
          scaleMax,
          placement,
          read: readLine('GPA', yourDisplay, cohortDisplay, placement),
        })
      }
    }
  }

  // ── GRE Quant ──
  const cohortGre = toNumber(cp.median_gre_quant)
  if (cohortGre != null) {
    const studentGre = pickTestScore(testScores, 'GRE', 'quant') ?? pickTestScore(testScores, 'GRE', 'Quant')
    if (studentGre != null) {
      const placement = placementOf(studentGre, cohortGre)
      const yourDisplay = trimDisplay(studentGre)
      const cohortDisplay = trimDisplay(cohortGre)
      out.push({
        key: 'gre_quant',
        label: 'GRE Quant',
        yourValue: studentGre,
        yourDisplay,
        cohortMedian: cohortGre,
        cohortDisplay,
        // GRE section scale tops out at 170 — gives the bar a real ceiling.
        scaleMax: 170,
        placement,
        read: readLine('GRE Quant', yourDisplay, cohortDisplay, placement),
      })
    }
  }

  // ── GMAT ──
  const cohortGmat = toNumber(cp.median_gmat)
  if (cohortGmat != null) {
    const studentGmat = pickTestScore(testScores, 'GMAT')
    if (studentGmat != null) {
      const placement = placementOf(studentGmat, cohortGmat)
      const yourDisplay = trimDisplay(studentGmat)
      const cohortDisplay = trimDisplay(cohortGmat)
      out.push({
        key: 'gmat',
        label: 'GMAT',
        yourValue: studentGmat,
        yourDisplay,
        cohortMedian: cohortGmat,
        cohortDisplay,
        // GMAT total tops out at 805 (current scale) — use 800 as a clean ceiling.
        scaleMax: 800,
        placement,
        read: readLine('GMAT', yourDisplay, cohortDisplay, placement),
      })
    }
  }

  return out
}

/** True when the cohort exposes at least one metric we *could* compare against,
 *  so the page can decide whether a "add your GPA to compare" nudge is worth it
 *  (we don't nudge when the cohort has nothing to compare to). */
export function cohortHasComparableMetric(classProfile: Record<string, unknown> | null | undefined): boolean {
  const cp = classProfile && typeof classProfile === 'object' ? classProfile : null
  if (!cp) return false
  return toNumber(cp.median_gpa) != null || toNumber(cp.median_gre_quant) != null || toNumber(cp.median_gmat) != null
}
