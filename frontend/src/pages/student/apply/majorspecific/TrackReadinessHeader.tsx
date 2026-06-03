// Spec 43 §4.18 — major-specific readiness header. The fit-score ring is the one
// earned gold beat: gold only at the "high"/"Strong" band, else cobalt
// (developing) / warning (getting started). Coverage map, specialization tags,
// suggested artifacts, and the bridge plan come from the MajorTrackCoach overlay
// (flag-gated). Feedback-only ethos: we surface gaps, never fill the field.
import clsx from 'clsx'
import { Compass, Lightbulb, Sparkles } from 'lucide-react'

import Card from '../../../../components/ui/Card'
import type { TrackCoach } from '../../../../types/majorSpecific'

import { BAND_META, SEVERITY_META } from './constants'

function ScoreRing({ score, band }: { score: number; band: TrackCoach['readiness_band'] }) {
  const meta = BAND_META[band] ?? BAND_META.low
  const r = 30
  const c = 2 * Math.PI * r
  const offset = c * (1 - Math.max(0, Math.min(100, score)) / 100)
  return (
    <div className="relative h-[76px] w-[76px] shrink-0">
      <svg viewBox="0 0 76 76" className="h-full w-full -rotate-90">
        <circle
          cx="38"
          cy="38"
          r={r}
          fill="none"
          stroke="currentColor"
          strokeWidth="7"
          className="text-muted-foreground"
        />
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
        <span className="text-[9px] uppercase tracking-wide text-muted-foreground">fit</span>
      </div>
    </div>
  )
}

export default function TrackReadinessHeader({ coach }: { coach: TrackCoach }) {
  const meta = BAND_META[coach.readiness_band] ?? BAND_META.low
  const severity = SEVERITY_META[coach.skill_gap_severity] ?? SEVERITY_META.none
  const coverage = Object.entries(coach.project_coverage_map)

  return (
    <Card variant="card-accent" className="space-y-4">
      <div className="flex flex-wrap items-center gap-4">
        <ScoreRing score={coach.major_track_fit_score} band={coach.readiness_band} />
        <div className="min-w-[160px] flex-1">
          <div className="flex items-center gap-1.5 text-eyebrow uppercase text-muted-foreground">
            <Compass size={13} /> Major-specific readiness
          </div>
          <div className={clsx('text-h3 font-bold', meta.text)}>{meta.label}</div>
          <p className="mt-0.5 text-sm text-muted-foreground">
            {coach.completeness}% of this track assessed
          </p>
        </div>
        <div className="flex flex-col items-end gap-1.5">
          <span className={clsx('rounded-full px-2.5 py-0.5 text-xs font-medium', severity.cls)}>
            {severity.label}
          </span>
          {coach.track_recommendation && (
            <span className="text-xs text-muted-foreground">
              Strongest fit: <span className="font-medium text-foreground">{coach.track_recommendation}</span>
            </span>
          )}
        </div>
      </div>

      {coverage.length > 0 && (
        <div className="space-y-1.5">
          <div className="text-eyebrow uppercase text-muted-foreground">Coverage by area</div>
          {coverage.map(([label, depth]) => (
            <div key={label} className="flex items-center gap-3">
              <span className="w-44 shrink-0 truncate text-xs text-muted-foreground">{label}</span>
              <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-muted">
                <div
                  className={clsx(
                    'h-full rounded-full transition-all duration-500',
                    depth >= 70 ? 'bg-primary' : depth >= 40 ? 'bg-secondary' : 'bg-warning',
                  )}
                  style={{ width: `${Math.max(2, depth)}%` }}
                />
              </div>
              <span className="w-8 shrink-0 text-right text-xs tabular-nums text-muted-foreground">
                {depth}
              </span>
            </div>
          ))}
        </div>
      )}

      {coach.specialization_match_tags.length > 0 && (
        <div>
          <div className="mb-1.5 text-eyebrow uppercase text-muted-foreground">
            Demonstrated strengths
          </div>
          <div className="flex flex-wrap gap-1.5">
            {coach.specialization_match_tags.map(t => (
              <span
                key={t}
                className="rounded-full bg-success-soft px-2.5 py-0.5 text-xs font-medium text-success"
              >
                {t}
              </span>
            ))}
          </div>
        </div>
      )}

      {coach.suggested_artifacts_to_add.length > 0 && (
        <div className="rounded-lg bg-muted px-3 py-2.5">
          <div className="mb-1 flex items-center gap-1.5 text-eyebrow uppercase text-muted-foreground">
            <Lightbulb size={13} /> Evidence to add
          </div>
          <ul className="ml-1 space-y-0.5">
            {coach.suggested_artifacts_to_add.map(a => (
              <li key={a} className="text-sm text-foreground">
                • {a}
              </li>
            ))}
          </ul>
        </div>
      )}

      {coach.suggested_bridge_plan && (
        <div className="flex items-start gap-2 rounded-lg bg-muted px-3 py-2.5">
          <Sparkles size={15} className="mt-0.5 shrink-0 text-primary" />
          <p className="text-sm text-foreground">{coach.suggested_bridge_plan}</p>
        </div>
      )}
    </Card>
  )
}
