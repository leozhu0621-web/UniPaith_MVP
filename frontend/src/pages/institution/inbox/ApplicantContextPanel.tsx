import { ExternalLink, ListChecks } from 'lucide-react'
import type { InstThread } from '../../../types'

// Spec 29 §3/§10 — applicant context rail. Surface + subtle elevation, cobalt
// links, no decorative imagery — editorial, dense, operational.
export default function ApplicantContextPanel({
  thread,
  onNavigate,
}: {
  thread: InstThread
  onNavigate: (path: string) => void
}) {
  const { context } = thread
  const hasChecklist = context.checklist_total > 0

  return (
    <aside className="rounded-xl border border-border bg-card p-3 shadow-sm">
      <p className="text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
        Applicant context
      </p>
      <p className="mt-1 text-sm font-semibold text-foreground">{thread.student.name}</p>
      {thread.program_name && (
        <p className="text-[11px] text-muted-foreground">{thread.program_name}</p>
      )}

      <dl className="mt-3 space-y-1.5 text-xs">
        {context.stage && (
          <div className="flex items-center justify-between gap-2">
            <dt className="text-muted-foreground">Stage</dt>
            <dd className="font-medium capitalize text-foreground">
              {context.stage.replace(/_/g, ' ')}
            </dd>
          </div>
        )}
        {hasChecklist && (
          <div className="flex items-center justify-between gap-2">
            <dt className="text-muted-foreground">Checklist</dt>
            <dd className="inline-flex items-center gap-1 font-medium text-foreground">
              <ListChecks size={12} className="text-cobalt" />
              {context.checklist_complete}/{context.checklist_total}
            </dd>
          </div>
        )}
      </dl>

      {context.missing_items.length > 0 && (
        <div className="mt-3">
          <p className="text-[11px] font-medium text-muted-foreground">Missing</p>
          <ul className="mt-1 space-y-0.5">
            {context.missing_items.map((item, i) => (
              <li key={i} className="truncate text-xs text-foreground">
                · {item}
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="mt-3 flex flex-col gap-1.5 border-t border-border pt-3">
        <button
          onClick={() => onNavigate(`/i/pipeline/${thread.student.id}`)}
          className="inline-flex items-center gap-1 text-xs font-medium text-cobalt hover:underline"
        >
          Open applicant <ExternalLink size={11} />
        </button>
        {thread.application_id && (
          <button
            onClick={() => onNavigate(`/i/pipeline/${thread.student.id}`)}
            className="inline-flex items-center gap-1 text-xs font-medium text-cobalt hover:underline"
          >
            Open checklist <ExternalLink size={11} />
          </button>
        )}
      </div>
    </aside>
  )
}
