import { AlertTriangle, CheckCircle2, Sparkles } from 'lucide-react'
import type { DatasetValidationReport } from '../../../types'
import Badge from '../../../components/ui/Badge'

// Spec 24 §7 — validation report: missing fields / duplicates / invalid dates /
// unmappable programs, each with the row indices the institution sees.
function rowList(rows: number[]): string {
  const shown = rows.slice(0, 12)
  return shown.join(', ') + (rows.length > shown.length ? ` +${rows.length - shown.length} more` : '')
}

export default function ValidationReportView({ report }: { report: DatasetValidationReport }) {
  const clean =
    report.missing_required.length === 0 &&
    report.duplicates.length === 0 &&
    report.invalid_dates.length === 0 &&
    report.unmappable_programs.length === 0

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        {clean ? (
          <CheckCircle2 size={18} className="text-success" />
        ) : (
          <AlertTriangle size={18} className="text-warning" />
        )}
        <p className="text-sm font-medium text-foreground">{report.summary}</p>
      </div>

      {report.triage_summary && (
        <div className="flex items-start gap-2 rounded-md border border-border bg-muted/60 p-3">
          <Sparkles size={14} className="mt-0.5 shrink-0 text-secondary" />
          <div>
            <p className="text-xs text-foreground">{report.triage_summary}</p>
            {report.triage_recommended_action && (
              <p className="mt-0.5 text-[11px] text-muted-foreground">
                Suggested: {report.triage_recommended_action.replace(/_/g, ' ')}
              </p>
            )}
          </div>
        </div>
      )}

      {!clean && (
        <div className="space-y-2 text-xs">
          {report.missing_required.length > 0 && (
            <div className="flex items-start gap-2">
              <Badge variant="warning">Missing fields</Badge>
              <span className="text-muted-foreground">
                {report.missing_required.length} rows · rows{' '}
                {rowList(report.missing_required.map((e) => e.row))}
              </span>
            </div>
          )}
          {report.duplicates.length > 0 && (
            <div className="flex items-start gap-2">
              <Badge variant="warning">Duplicates</Badge>
              <span className="text-muted-foreground">
                {report.duplicates.length} rows · rows {rowList(report.duplicates.map((e) => e.row))}
              </span>
            </div>
          )}
          {report.invalid_dates.length > 0 && (
            <div className="flex items-start gap-2">
              <Badge variant="warning">Invalid dates</Badge>
              <span className="text-muted-foreground">
                {report.invalid_dates.length} · e.g. row {report.invalid_dates[0].row} ={' '}
                <code className="text-foreground">{report.invalid_dates[0].value}</code>
              </span>
            </div>
          )}
          {report.unmappable_programs.length > 0 && (
            <div className="flex items-start gap-2">
              <Badge variant="warning">Unmapped programs</Badge>
              <span className="text-muted-foreground">
                {report.unmappable_programs.length} · e.g. “{report.unmappable_programs[0].value}”
                {report.unmappable_programs[0].suggestions.length > 0 && (
                  <> → did you mean “{report.unmappable_programs[0].suggestions[0]}”?</>
                )}
              </span>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
