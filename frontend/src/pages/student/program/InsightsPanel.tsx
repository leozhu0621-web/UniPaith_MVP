/**
 * Insights — Spec 11 §3.5. The single most important tab: the human signal the
 * cards can't carry. Two panels in one place (per §3.6 the spec considers
 * Reviews + Employer Feedback ONE tab):
 *
 *   1. Student / alumni reviews — overall + per-dimension, reviewer-context tags,
 *      guided prompts, who-thrives callouts.
 *   2. Professional / employer feedback — job-readiness sentiment, skill
 *      dimensions, hiring behavior, derived summary themes.
 *
 * Filters are controlled by the parent so they persist in the URL (§10).
 *
 * Brand: editorial. Cobalt is the only data-viz hue (per §8 "use --secondary for
 * the primary series only"); no gradients, no marketing color. Ratings render as
 * cobalt — gold stays reserved for the DualRing.
 */
import { Star, Quote, Briefcase, Users, MessageSquareText, Building2, TrendingUp } from 'lucide-react'
import Card from '../../../components/ui/Card'
import Badge from '../../../components/ui/Badge'
import { formatDate } from '../../../utils/format'
import type {
  ProgramReviewSummary,
  EmployerFeedbackSummary,
  ProgramReview,
} from '../../../types'

// Per-dimension labels (review + employer skill dims) per §3.5.
const REVIEW_DIMS: { key: keyof ProgramReviewSummary; label: string }[] = [
  { key: 'avg_teaching', label: 'Teaching quality' },
  { key: 'avg_workload', label: 'Workload' },
  { key: 'avg_career_support', label: 'Career support' },
  { key: 'avg_internship_access', label: 'Internship access' },
  { key: 'avg_community_culture', label: 'Community & culture' },
  { key: 'avg_roi', label: 'Perceived ROI' },
]
const EMPLOYER_DIMS: { key: keyof EmployerFeedbackSummary; label: string }[] = [
  { key: 'avg_technical', label: 'Technical fundamentals' },
  { key: 'avg_practical', label: 'Practical skills' },
  { key: 'avg_communication', label: 'Communication' },
  { key: 'avg_teamwork', label: 'Teamwork' },
  { key: 'avg_reliability', label: 'Reliability' },
]

const GUIDED_PROMPTS = ['Who thrives here', 'Who should avoid it', 'Best resources', 'Biggest tradeoffs']

const EMPTY_REVIEWS_COPY = "Reviews aren't available for this program yet."

/* ── Small presentational helpers ─────────────────────────────────────────── */

function Stars({ value }: { value: number | null }) {
  if (value == null) return null
  const v = Math.round(value)
  return (
    <span className="inline-flex items-center gap-0.5" aria-label={`${value} out of 5`}>
      {Array.from({ length: 5 }).map((_, i) => (
        <Star
          key={i}
          size={12}
          className={i < v ? 'text-cobalt fill-cobalt' : 'text-stone'}
        />
      ))}
    </span>
  )
}

function DimBar({ label, value }: { label: string; value: number | null }) {
  if (value == null) return null
  return (
    <div className="flex items-center gap-3">
      <span className="text-xs text-student-text w-36 flex-shrink-0">{label}</span>
      <div className="flex-1 h-2 bg-student-mist rounded-pill overflow-hidden">
        <div className="h-full bg-cobalt rounded-pill" style={{ width: `${(value / 5) * 100}%` }} />
      </div>
      <span className="text-xs font-semibold text-student-ink w-8 text-right tabular-nums">
        {value.toFixed(1)}
      </span>
    </div>
  )
}

/* ── Reviewer-context readers (defensive — context shape varies) ──────────── */

const ctxStr = (ctx: Record<string, unknown> | null, ...keys: string[]): string => {
  if (!ctx) return ''
  for (const k of keys) {
    const v = ctx[k]
    if (v != null && v !== '') return String(v)
  }
  return ''
}
const reviewerTypeOf = (r: ProgramReview) =>
  ctxStr(r.reviewer_context, 'status', 'reviewer_type', 'type')
const degreeOf = (r: ProgramReview) => ctxStr(r.reviewer_context, 'degree', 'degree_level')
const cohortOf = (r: ProgramReview) =>
  ctxStr(r.reviewer_context, 'cohort_year', 'graduation_year', 'year')

const titleCase = (s: string) => s.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())

/* ── Derived summary themes (§3.5) — deterministic, from real averages only ── */

function extremes(
  dims: { label: string; value: number | null }[],
): { hi?: { label: string; value: number }; lo?: { label: string; value: number } } {
  const present = dims.filter(d => d.value != null) as { label: string; value: number }[]
  if (present.length < 2) return {}
  const sorted = [...present].sort((a, b) => b.value - a.value)
  return { hi: sorted[0], lo: sorted[sorted.length - 1] }
}

interface Props {
  programName: string
  reviews: ProgramReviewSummary | null
  employer: EmployerFeedbackSummary | null
  // Controlled filters (persisted in the URL by the parent).
  reviewerType: string
  degree: string
  cohort: string
  minRating: string
  industry: string
  onFilter: (key: 'reviewer' | 'degree' | 'cohort' | 'dim' | 'industry', value: string) => void
  onClear: () => void
  onWriteReview?: () => void
  similarPrograms?: { id: string; program_name: string; institution_name?: string | null }[]
  onNavigateProgram?: (id: string) => void
}

export default function InsightsPanel({
  programName,
  reviews,
  employer,
  reviewerType,
  degree,
  cohort,
  minRating,
  industry,
  onFilter,
  onClear,
  onWriteReview,
  similarPrograms = [],
  onNavigateProgram,
}: Props) {
  const allReviews = reviews?.reviews ?? []
  const totalReviews = reviews?.total_reviews ?? 0
  const allFeedback = employer?.feedback ?? []
  const totalFeedback = employer?.total_feedback ?? 0

  // Filter option sets, derived from the data.
  const reviewerTypes = [...new Set(allReviews.map(reviewerTypeOf).filter(Boolean))]
  const degrees = [...new Set(allReviews.map(degreeOf).filter(Boolean))]
  const cohorts = [...new Set(allReviews.map(cohortOf).filter(Boolean))].sort()
  const industries = [...new Set(allFeedback.map(f => f.industry).filter(Boolean) as string[])]

  const filteredReviews = allReviews.filter(r => {
    if (reviewerType && reviewerTypeOf(r) !== reviewerType) return false
    if (degree && degreeOf(r) !== degree) return false
    if (cohort && cohortOf(r) !== cohort) return false
    if (minRating && (r.rating_overall ?? 0) < Number(minRating)) return false
    return true
  })
  const filteredFeedback = allFeedback.filter(f => !industry || f.industry === industry)

  // Derived themes.
  const revEx = extremes(REVIEW_DIMS.map(d => ({ label: d.label, value: (reviews?.[d.key] as number | null) ?? null })))
  const empEx = extremes(EMPLOYER_DIMS.map(d => ({ label: d.label, value: (employer?.[d.key] as number | null) ?? null })))
  const sentiments = employer?.sentiment_counts ?? {}
  const sentTotal = Object.values(sentiments).reduce((s, v) => s + (Number(v) || 0), 0)
  const positivePct = sentTotal > 0 ? Math.round(((sentiments.positive ?? 0) / sentTotal) * 100) : null

  const studentsSay =
    totalReviews > 0 && revEx.hi
      ? `Rated strongest for ${revEx.hi.label.toLowerCase()} (${revEx.hi.value.toFixed(1)}/5)${
          revEx.lo ? `, weakest for ${revEx.lo.label.toLowerCase()} (${revEx.lo.value.toFixed(1)}/5)` : ''
        }.`
      : null
  const employersSay =
    totalFeedback > 0 && empEx.hi
      ? `Employers rate ${empEx.hi.label.toLowerCase()} strongest (${empEx.hi.value.toFixed(1)}/5)${
          positivePct != null ? `; ${positivePct}% of feedback is positive` : ''
        }.`
      : null
  const tradeoffs =
    revEx.hi && revEx.lo && revEx.hi.label !== revEx.lo.label
      ? `Students praise ${revEx.hi.label.toLowerCase()} but flag ${revEx.lo.label.toLowerCase()}.`
      : empEx.hi && empEx.lo && empEx.hi.label !== empEx.lo.label
        ? `Employers value ${empEx.hi.label.toLowerCase()} most and ${empEx.lo.label.toLowerCase()} least.`
        : null

  const hasThemes = !!(studentsSay || employersSay || tradeoffs)
  const filtersActive = !!(reviewerType || degree || cohort || minRating)

  return (
    <div className="space-y-4">
      {/* ── Summary themes (§3.5) ── */}
      {hasThemes && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          {[
            { icon: Users, title: 'What students say', body: studentsSay },
            { icon: Briefcase, title: 'What employers say', body: employersSay },
            { icon: TrendingUp, title: 'Common tradeoffs', body: tradeoffs },
          ]
            .filter(t => t.body)
            .map((t, i) => (
              <div key={i} className="rounded-lg border border-divider bg-student-mist/50 p-3">
                <div className="flex items-center gap-1.5 mb-1.5">
                  <t.icon size={13} className="text-cobalt" />
                  <p className="text-[11px] font-semibold uppercase tracking-wide text-student-text">
                    {t.title}
                  </p>
                </div>
                <p className="text-xs text-student-ink leading-relaxed">{t.body}</p>
              </div>
            ))}
        </div>
      )}

      {/* ══ Panel 1 — Student / alumni reviews ══ */}
      <Card className="p-5">
        <div className="flex items-center gap-2 mb-1">
          <MessageSquareText size={15} className="text-cobalt" />
          <h3 className="font-semibold text-student-ink">Student &amp; alumni reviews</h3>
          {totalReviews > 0 && reviews?.avg_overall != null && (
            <span className="ml-auto flex items-center gap-1.5">
              <Stars value={reviews.avg_overall} />
              <span className="text-sm font-bold text-student-ink tabular-nums">
                {reviews.avg_overall.toFixed(1)}
              </span>
              <span className="text-xs text-student-text">
                · {totalReviews} review{totalReviews !== 1 ? 's' : ''}
              </span>
            </span>
          )}
        </div>

        {/* Guided prompts (§3.5) */}
        <div className="flex flex-wrap items-center gap-1.5 mb-4">
          <span className="text-[11px] text-student-text/70">Reviews answer:</span>
          {GUIDED_PROMPTS.map(p => (
            <span key={p} className="text-[11px] px-2 py-0.5 rounded-pill bg-student-mist text-student-text">
              {p}
            </span>
          ))}
        </div>

        {totalReviews > 0 ? (
          <>
            {/* Per-dimension averages */}
            <div className="space-y-2 mb-4">
              {REVIEW_DIMS.map(d => (
                <DimBar key={String(d.key)} label={d.label} value={(reviews?.[d.key] as number | null) ?? null} />
              ))}
            </div>

            {/* Filters — reviewer type / degree / cohort / rating dimension */}
            <div className="flex flex-wrap gap-2 mb-3">
              {reviewerTypes.length > 0 && (
                <select
                  aria-label="Filter by reviewer type"
                  value={reviewerType}
                  onChange={e => onFilter('reviewer', e.target.value)}
                  className="text-xs border border-stone rounded-md px-2 py-1.5 bg-white"
                >
                  <option value="">All reviewers</option>
                  {reviewerTypes.map(t => <option key={t} value={t}>{titleCase(t)}</option>)}
                </select>
              )}
              {degrees.length > 0 && (
                <select
                  aria-label="Filter by degree level"
                  value={degree}
                  onChange={e => onFilter('degree', e.target.value)}
                  className="text-xs border border-stone rounded-md px-2 py-1.5 bg-white"
                >
                  <option value="">All degrees</option>
                  {degrees.map(d => <option key={d} value={d}>{titleCase(d)}</option>)}
                </select>
              )}
              {cohorts.length > 0 && (
                <select
                  aria-label="Filter by cohort year"
                  value={cohort}
                  onChange={e => onFilter('cohort', e.target.value)}
                  className="text-xs border border-stone rounded-md px-2 py-1.5 bg-white"
                >
                  <option value="">All cohorts</option>
                  {cohorts.map(c => <option key={c} value={c}>{c}</option>)}
                </select>
              )}
              <select
                aria-label="Filter by minimum rating"
                value={minRating}
                onChange={e => onFilter('dim', e.target.value)}
                className="text-xs border border-stone rounded-md px-2 py-1.5 bg-white"
              >
                <option value="">Any rating</option>
                <option value="4">4+ stars</option>
                <option value="3">3+ stars</option>
                <option value="2">2+ stars</option>
              </select>
              {filtersActive && (
                <button onClick={onClear} className="text-xs text-cobalt hover:underline px-1">
                  Clear
                </button>
              )}
            </div>

            {/* Review cards */}
            {filteredReviews.length > 0 ? (
              <div className="space-y-3">
                {filteredReviews.map(r => (
                  <div key={r.id} className="rounded-lg border border-divider p-4">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <Stars value={r.rating_overall} />
                        {r.is_verified && <Badge variant="success" size="sm">Verified</Badge>}
                      </div>
                      <span className="text-[10px] text-student-text/60">{formatDate(r.created_at)}</span>
                    </div>
                    {r.reviewer_context && (
                      <div className="flex flex-wrap gap-1.5 mb-2">
                        {[reviewerTypeOf(r), degreeOf(r), cohortOf(r)].filter(Boolean).map((v, i) => (
                          <Badge key={i} variant="neutral" size="sm">{titleCase(v)}</Badge>
                        ))}
                      </div>
                    )}
                    {r.review_text && <p className="text-sm text-student-text mb-2">{r.review_text}</p>}
                    {r.who_thrives_here && (
                      <div className="bg-student-mist rounded-lg p-3 mt-2">
                        <div className="flex items-center gap-1.5 mb-1">
                          <Quote size={12} className="text-cobalt" />
                          <span className="text-xs font-semibold text-cobalt">Who thrives here</span>
                        </div>
                        <p className="text-xs text-student-text">{r.who_thrives_here}</p>
                      </div>
                    )}
                    {(r.external_source as { source?: string } | null)?.source && (
                      <p className="text-[10px] text-student-text/50 mt-2 italic">
                        Source: {String((r.external_source as { source?: string }).source)}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-student-text">No reviews match these filters.</p>
            )}
          </>
        ) : (
          /* Empty state — canonical copy per §11 */
          <div className="rounded-lg border border-divider p-5">
            <p className="text-sm font-medium text-student-ink">{EMPTY_REVIEWS_COPY}</p>
            <p className="text-xs text-student-text mt-1">
              Studied here? Share what it's like — reviews stay anonymous unless you opt in.
            </p>
            {onWriteReview && (
              <button
                onClick={onWriteReview}
                className="mt-3 px-3 py-1.5 text-xs font-semibold bg-cobalt text-white rounded-md hover:bg-cobalt-hover transition-colors"
              >
                Write a review
              </button>
            )}
            {similarPrograms.length > 0 && onNavigateProgram && (
              <div className="mt-4">
                <p className="text-[11px] text-student-text/70 mb-2">See reviews for similar programs:</p>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                  {similarPrograms.slice(0, 4).map(sp => (
                    <button
                      key={sp.id}
                      onClick={() => onNavigateProgram(sp.id)}
                      className="flex items-center justify-between gap-2 px-3 py-2 rounded-md border border-divider hover:border-cobalt hover:bg-student-mist transition-colors text-left"
                    >
                      <div className="min-w-0">
                        <p className="text-xs font-medium text-student-ink truncate">{sp.program_name}</p>
                        {sp.institution_name && (
                          <p className="text-[10px] text-student-text/70 truncate">{sp.institution_name}</p>
                        )}
                      </div>
                      <Star size={12} className="text-student-text/40 flex-shrink-0" />
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </Card>

      {/* ══ Panel 2 — Professional / employer feedback ══ */}
      <Card className="p-5">
        <div className="flex items-center gap-2 mb-4">
          <Briefcase size={15} className="text-cobalt" />
          <h3 className="font-semibold text-student-ink">Employer feedback</h3>
          {totalFeedback > 0 && (
            <span className="ml-auto text-xs text-student-text">
              {totalFeedback} employer{totalFeedback !== 1 ? 's' : ''}
            </span>
          )}
        </div>

        {totalFeedback > 0 ? (
          <>
            {/* Job-readiness sentiment — single cobalt-intensity series (§8) */}
            {sentTotal > 0 && (
              <div className="mb-4">
                <p className="text-xs text-student-text mb-2">Job-readiness sentiment</p>
                <div className="flex h-3 rounded-pill overflow-hidden bg-student-mist">
                  {([
                    ['positive', 'bg-cobalt'],
                    ['neutral', 'bg-cobalt/40'],
                    ['negative', 'bg-cobalt/15'],
                  ] as const).map(([key, cls]) => {
                    const c = Number(sentiments[key] ?? 0)
                    if (!c) return null
                    return <div key={key} className={cls} style={{ width: `${(c / sentTotal) * 100}%` }} />
                  })}
                </div>
                <div className="flex gap-4 mt-2">
                  {(['positive', 'neutral', 'negative'] as const).map(key => (
                    <span key={key} className="flex items-center gap-1.5 text-[11px] text-student-text">
                      <span
                        className={`w-2 h-2 rounded-full ${
                          key === 'positive' ? 'bg-cobalt' : key === 'neutral' ? 'bg-cobalt/40' : 'bg-cobalt/15'
                        }`}
                      />
                      {key} ({Number(sentiments[key] ?? 0)})
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Skill dimensions */}
            <div className="space-y-2 mb-4">
              {EMPLOYER_DIMS.map(d => (
                <DimBar key={String(d.key)} label={d.label} value={(employer?.[d.key] as number | null) ?? null} />
              ))}
            </div>

            {/* Industry filter */}
            {industries.length > 0 && (
              <div className="flex items-center gap-2 mb-3">
                <select
                  aria-label="Filter by industry"
                  value={industry}
                  onChange={e => onFilter('industry', e.target.value)}
                  className="text-xs border border-stone rounded-md px-2 py-1.5 bg-white"
                >
                  <option value="">All industries</option>
                  {industries.map(i => <option key={i} value={i}>{i}</option>)}
                </select>
                {industry && (
                  <button onClick={() => onFilter('industry', '')} className="text-xs text-cobalt hover:underline">
                    Clear
                  </button>
                )}
              </div>
            )}

            {/* Feedback cards (incl. hiring behavior) */}
            <div className="space-y-3">
              {filteredFeedback.map(f => (
                <div key={f.id} className="rounded-lg border border-divider p-4">
                  <div className="flex items-center justify-between mb-1.5">
                    <div className="flex items-center gap-2">
                      <Building2 size={13} className="text-student-text/50" />
                      <p className="text-sm font-medium text-student-ink">{f.employer_name}</p>
                    </div>
                    <div className="flex items-center gap-2">
                      {f.industry && <Badge variant="info" size="sm">{f.industry}</Badge>}
                      {f.feedback_year && (
                        <span className="text-[10px] text-student-text/60">{f.feedback_year}</span>
                      )}
                    </div>
                  </div>
                  {f.feedback_text && <p className="text-sm text-student-text">{f.feedback_text}</p>}
                  {f.hiring_pattern && (
                    <p className="text-[11px] text-student-text mt-2 flex items-center gap-1.5 bg-student-mist rounded-md px-2 py-1">
                      <Briefcase size={11} className="text-cobalt" />
                      {f.hiring_pattern}
                    </p>
                  )}
                </div>
              ))}
              {filteredFeedback.length === 0 && (
                <p className="text-sm text-student-text">No employer feedback matches this filter.</p>
              )}
            </div>
          </>
        ) : (
          <p className="text-sm text-student-text">
            Employer feedback isn't available for {programName} yet.
          </p>
        )}
      </Card>
    </div>
  )
}
