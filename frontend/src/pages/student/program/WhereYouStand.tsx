import { Link } from 'react-router-dom'
import { Compass } from 'lucide-react'

import type { AcademicRecord, TestScore } from '../../../types'
import { buildStandComparisons, cohortHasComparableMetric } from './standComparison'

interface Props {
  classProfile: Record<string, unknown> | null | undefined
  academicRecords: AcademicRecord[] | undefined
  testScores: TestScore[] | undefined
}

/**
 * "Where you stand" — relates the cohort's median anchors to the student's own
 * numbers, the core fit insight ("fit, not fame"). Renders inside the Class
 * Profile card, directly beside the numbers it compares against.
 *
 * Graceful by design:
 *  - a metric row appears only when BOTH the cohort median and the student's
 *    value exist; everything else is omitted silently.
 *  - if the cohort has comparable metrics but the student has entered none, a
 *    quiet nudge points to the profile — never a fabricated comparison.
 *  - if the cohort exposes nothing comparable, the whole block is omitted.
 */
export default function WhereYouStand({ classProfile, academicRecords, testScores }: Props) {
  const comparisons = buildStandComparisons({ classProfile, academicRecords, testScores })

  if (comparisons.length === 0) {
    // Only nudge when there's actually something to compare against.
    if (!cohortHasComparableMetric(classProfile)) return null
    return (
      <div className="mt-4 pt-4 border-t border-border">
        <div className="flex items-center gap-2 mb-1.5">
          <Compass size={13} className="text-secondary" />
          <h4 className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">Where you stand</h4>
        </div>
        <p className="text-sm text-muted-foreground">
          Add your GPA or test scores in your{' '}
          <Link to="/s/profile?tab=academics" className="text-secondary hover:underline">
            profile
          </Link>{' '}
          to see how you compare with this cohort.
        </p>
      </div>
    )
  }

  return (
    <div className="mt-4 pt-4 border-t border-border">
      <div className="flex items-center gap-2 mb-3">
        <Compass size={13} className="text-secondary" />
        <h4 className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">Where you stand</h4>
      </div>
      <div className="space-y-3.5">
        {comparisons.map((c) => {
          const yourPct = Math.max(0, Math.min(100, (c.yourValue / c.scaleMax) * 100))
          const medianPct = Math.max(0, Math.min(100, (c.cohortMedian / c.scaleMax) * 100))
          return (
            <div key={c.key}>
              <div className="flex items-baseline justify-between gap-2 mb-1.5">
                <span className="text-xs font-semibold text-foreground">{c.label}</span>
                <span className="text-[11px] tabular-nums text-muted-foreground">
                  You {c.yourDisplay} · Median {c.cohortDisplay}
                </span>
              </div>
              {/* Bar: cobalt fill to the student's value, a marker at the cohort
                  median. Decorative — the read line below carries the meaning. */}
              <div className="relative w-full bg-muted rounded-pill h-2 overflow-visible" aria-hidden="true">
                <div
                  className="absolute left-0 top-0 h-2 rounded-pill bg-secondary transition-all duration-300"
                  style={{ width: `${yourPct}%` }}
                />
                <span
                  className="absolute top-[-2px] h-3 w-[2px] rounded-pill bg-foreground"
                  style={{ left: `calc(${medianPct}% - 1px)` }}
                  title={`Cohort median: ${c.cohortDisplay}`}
                />
              </div>
              <p className="mt-1.5 text-sm text-foreground/80 leading-snug">{c.read}</p>
            </div>
          )
        })}
      </div>
    </div>
  )
}
