import { AlertTriangle, Users } from 'lucide-react'
import type { SegmentPreview } from '../../../types'
import { FIT_BAND_LABEL } from './helpers'

interface Props {
  preview: SegmentPreview | undefined
  loading: boolean
  hasRun: boolean
}

/** Spec 26 §3/§8/§9 — audience size (in --accent), 10-row sample (02 §8),
 *  composition, and the fairness skew warning. Handles loading + zero-match. */
export default function AudiencePreview({ preview, loading, hasRun }: Props) {
  if (loading) {
    return (
      <div className="flex items-center gap-3 rounded-lg border border-border bg-surface p-4">
        <span className="h-4 w-4 animate-spin rounded-full border-2 border-cobalt border-t-transparent" />
        <span className="text-sm text-muted-foreground">Calculating audience…</span>
      </div>
    )
  }

  if (!hasRun || !preview) {
    return (
      <div className="rounded-lg border border-dashed border-border bg-surface p-4 text-sm text-muted-foreground">
        Add rules and press <span className="font-medium text-foreground">Preview audience</span> to
        see how many students match.
      </div>
    )
  }

  if (preview.audience_count === 0) {
    return (
      <div className="rounded-lg border border-border bg-surface p-4">
        <p className="text-sm font-medium text-foreground">0 students match these rules.</p>
        <p className="text-sm text-muted-foreground">Try widening criteria.</p>
      </div>
    )
  }

  return (
    <div className="space-y-3 rounded-lg border border-border bg-surface p-4">
      {/* Headline count — the key metric, in --accent (cobalt) */}
      <div className="flex items-baseline gap-2">
        <Users size={18} className="text-cobalt" />
        <span className="text-3xl font-bold text-cobalt tabular-nums">
          {preview.audience_count.toLocaleString()}
        </span>
        <span className="text-sm text-muted-foreground">students match</span>
        {preview.uploaded_external_count > 0 && (
          <span className="text-xs text-muted-foreground">
            ({preview.platform_count.toLocaleString()} on platform +{' '}
            {preview.uploaded_external_count.toLocaleString()} from uploaded lists)
          </span>
        )}
      </div>

      {/* Fairness skew warning (§13 / 46 §6) */}
      {preview.fairness_warning && (
        <div className="flex items-start gap-2 rounded-md bg-warning-soft px-3 py-2 text-sm text-warning">
          <AlertTriangle size={15} className="mt-0.5 shrink-0" />
          <span>{preview.fairness_warning}</span>
        </div>
      )}

      {/* Composition */}
      {Object.keys(preview.composition).length > 0 && (
        <div className="flex flex-wrap gap-4 text-xs text-muted-foreground">
          {Object.entries(preview.composition).map(([attr, dist]) => {
            const top = Object.entries(dist)
              .sort((a, b) => b[1] - a[1])
              .slice(0, 3)
            return (
              <div key={attr}>
                <span className="font-semibold capitalize">{attr.replace(/_/g, ' ')}:</span>{' '}
                {top.map(([k, v]) => `${k} ${v}`).join(' · ')}
              </div>
            )
          })}
        </div>
      )}

      {/* Sample table (02 §8) */}
      {preview.sample.length > 0 && (
        <div className="overflow-hidden rounded-md border border-border">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-muted text-[11px] uppercase tracking-wide text-muted-foreground">
                <th className="px-3 py-2 text-left font-semibold">Student</th>
                <th className="px-3 py-2 text-left font-semibold">Nationality</th>
                <th className="px-3 py-2 text-left font-semibold">Fit</th>
              </tr>
            </thead>
            <tbody>
              {preview.sample.map((s) => (
                <tr key={s.student_id} className="border-t border-border hover:bg-muted/50">
                  <td className="px-3 py-2">{s.name}</td>
                  <td className="px-3 py-2 text-muted-foreground">{s.nationality ?? '—'}</td>
                  <td className="px-3 py-2">
                    {s.fit_band ? (
                      <span
                        className={[
                          'rounded-full px-2 py-0.5 text-xs',
                          s.fit_band === 'high'
                            ? 'bg-success-soft text-success'
                            : s.fit_band === 'medium'
                              ? 'bg-cobalt/10 text-cobalt'
                              : 'bg-muted text-muted-foreground',
                        ].join(' ')}
                      >
                        {FIT_BAND_LABEL[s.fit_band] ?? s.fit_band}
                      </span>
                    ) : (
                      <span className="text-muted-foreground">—</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="bg-muted/40 px-3 py-1.5 text-[11px] text-muted-foreground">
            Showing {preview.sample.length} of {preview.audience_count.toLocaleString()}
          </p>
        </div>
      )}
    </div>
  )
}
