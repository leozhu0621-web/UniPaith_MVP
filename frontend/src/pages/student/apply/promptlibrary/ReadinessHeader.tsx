// Spec 42 §4.17 — readiness header. The interview-readiness ring is the one
// earned gold beat: it turns gold only when readiness reaches "high". Otherwise
// cobalt (functional) / warning (low). Competency coverage + practice plan come
// from the PromptCoach overlay when the AI surface is enabled.
import clsx from 'clsx'
import { Sparkles, Target } from 'lucide-react'

import Card from '../../../../components/ui/Card'
import type { PromptLibrarySummary } from '../../../../types/promptLibrary'

import { COMPETENCY_LABELS, COMPETENCIES } from './constants'

const BAND_META: Record<string, { label: string; ring: string; text: string }> = {
  high: { label: 'Interview-ready', ring: 'text-primary', text: 'text-primary' },
  medium: { label: 'Getting there', ring: 'text-secondary', text: 'text-secondary' },
  low: { label: 'Just starting', ring: 'text-warning', text: 'text-warning' },
}

function ScoreRing({ score, band }: { score: number; band: string }) {
  const meta = BAND_META[band] ?? BAND_META.low
  const r = 30
  const c = 2 * Math.PI * r
  const offset = c * (1 - Math.max(0, Math.min(100, score)) / 100)
  return (
    <div className="relative h-[76px] w-[76px] shrink-0">
      <svg viewBox="0 0 76 76" className="h-full w-full -rotate-90">
        <circle cx="38" cy="38" r={r} fill="none" stroke="currentColor" strokeWidth="7" className="text-muted-foreground" />
        <circle
          cx="38"
          cy="38"
          r={r}
          fill="none"
          stroke="currentColor"
          strokeWidth="7"
          strokeLinecap="round"
          strokeDasharray={c}
          strokeDashoffset={offset}
          className={clsx('transition-all duration-700 ease-out', meta.ring)}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className={clsx('text-lg font-bold leading-none', meta.text)}>{score}</span>
        <span className="text-[9px] uppercase tracking-wide text-muted-foreground">score</span>
      </div>
    </div>
  )
}

export default function ReadinessHeader({ summary }: { summary: PromptLibrarySummary }) {
  const band = summary.interview_readiness_band
  const score = summary.interview_readiness_score
  const meta = band ? BAND_META[band] : null
  const gaps = new Set(summary.competency_coverage_gaps ?? [])

  return (
    <Card variant="card-accent" className="space-y-4">
      <div className="flex flex-wrap items-center gap-4">
        {summary.inference_enabled && band != null && score != null ? (
          <>
            <ScoreRing score={score} band={band} />
            <div className="min-w-[140px] flex-1">
              <div className="flex items-center gap-1.5 text-eyebrow uppercase text-muted-foreground">
                <Target size={13} /> Interview readiness
              </div>
              <div className={clsx('text-h3 font-bold', meta?.text)}>{meta?.label}</div>
              <p className="mt-0.5 text-sm text-muted-foreground">
                {summary.readiness_detail
                  ? `${summary.readiness_detail.answered}/${summary.readiness_detail.core_total} core questions answered`
                  : null}
              </p>
            </div>
          </>
        ) : (
          <div className="flex-1">
            <div className="text-eyebrow uppercase text-muted-foreground">Your practice</div>
            <div className="text-h3 font-bold text-foreground">
              {summary.answered_count} of {summary.total_prompts} prompts answered
            </div>
          </div>
        )}

        <div className="flex gap-5">
          <Stat label="Answered" value={summary.answered_count} />
          <Stat label="Final" value={summary.final_count} />
          <Stat label="Stories" value={summary.stories_count} />
        </div>
      </div>

      {summary.inference_enabled && summary.competency_coverage_map && (
        <div>
          <div className="mb-1.5 text-eyebrow uppercase text-muted-foreground">Competency coverage</div>
          <div className="flex flex-wrap gap-1.5">
            {COMPETENCIES.map(c => {
              const covered = !gaps.has(c)
              return (
                <span
                  key={c}
                  className={clsx(
                    'rounded-full px-2.5 py-0.5 text-xs font-medium',
                    covered
                      ? 'bg-success-soft text-success'
                      : 'bg-warning-soft text-warning',
                  )}
                >
                  {COMPETENCY_LABELS[c]}
                </span>
              )
            })}
          </div>
        </div>
      )}

      {summary.inference_enabled && summary.suggested_practice_plan && (
        <div className="flex items-start gap-2 rounded-lg bg-muted px-3 py-2.5">
          <Sparkles size={15} className="mt-0.5 shrink-0 text-primary" />
          <p className="text-sm text-foreground">{summary.suggested_practice_plan}</p>
        </div>
      )}
    </Card>
  )
}

function Stat({ label, value }: { label: string; value: number }) {
  return (
    <div className="text-center">
      <div className="text-xl font-bold text-foreground">{value}</div>
      <div className="text-eyebrow uppercase text-muted-foreground">{label}</div>
    </div>
  )
}
