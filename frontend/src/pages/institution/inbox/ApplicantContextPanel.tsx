import { ExternalLink } from 'lucide-react'
import type { InstInboxThread } from '../../../types'

export default function ApplicantContextPanel({
  thread,
  onOpenApplicant,
  onOpenChecklist,
}: {
  thread: InstInboxThread
  onOpenApplicant: (applicationId: string) => void
  onOpenChecklist: (applicationId: string) => void
}) {
  const ctx = thread.context
  const appLabel = thread.application_id ? `App · ${thread.application_id.slice(0, 8)}` : 'Pre-application inquiry'

  return (
    <aside className="flex h-full w-72 shrink-0 flex-col border-l border-border bg-muted/30 p-4">
      <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Context</p>
      <div className="mt-3 rounded-lg border border-border bg-card p-3 shadow-sm">
        <p className="text-sm font-medium text-foreground">{appLabel}</p>
        {ctx.stage && (
          <p className="mt-1 text-xs text-muted-foreground">
            Stage: <span className="text-foreground">{ctx.stage}</span>
          </p>
        )}
        <p className="mt-2 text-xs text-muted-foreground">
          Checklist {ctx.checklist_complete}/{ctx.checklist_total || '—'}
        </p>
        {ctx.missing_items.length > 0 && (
          <div className="mt-2">
            <p className="text-[10px] font-medium uppercase text-muted-foreground">Missing</p>
            <ul className="mt-1 space-y-0.5 text-xs text-foreground">
              {ctx.missing_items.map(item => (
                <li key={item} className="truncate">
                  {item}
                </li>
              ))}
            </ul>
          </div>
        )}
        <div className="mt-3 flex flex-col gap-2">
          {thread.application_id && (
            <>
              <button
                type="button"
                onClick={() => onOpenApplicant(thread.application_id!)}
                className="inline-flex items-center gap-1 text-xs font-medium text-cobalt hover:underline"
              >
                Open applicant <ExternalLink size={12} />
              </button>
              <button
                type="button"
                onClick={() => onOpenChecklist(thread.application_id!)}
                className="inline-flex items-center gap-1 text-xs font-medium text-cobalt hover:underline"
              >
                Open checklist <ExternalLink size={12} />
              </button>
            </>
          )}
        </div>
      </div>
      {thread.status === 'awaiting_us' && !thread.assigned_to && (
        <p className="mt-4 text-xs text-warning">Assign to yourself to respond.</p>
      )}
    </aside>
  )
}
