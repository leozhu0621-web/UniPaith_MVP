// Applied-status pill for discovery cards (Discover review 2026-06-19, benchmark
// lens). Handshake/LinkedIn label a job you've already acted on wherever it
// reappears — so a re-encountered program shows its real pipeline stage. Data is
// the live application record (no fabrication): status comes straight from
// /applications/me. The pill renders only when an application actually exists.
import { useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { CircleCheck, CircleDashed } from 'lucide-react'
import { listMyApplications } from '../../../../api/applications'

export type AppStatus = 'draft' | 'submitted' | 'under_review' | 'interview' | 'decision_made'

const STAGE: Record<AppStatus, { label: string; applied: boolean }> = {
  draft: { label: 'Draft', applied: false },
  submitted: { label: 'Applied', applied: true },
  under_review: { label: 'In review', applied: true },
  interview: { label: 'Interview', applied: true },
  decision_made: { label: 'Decision', applied: true },
}

/**
 * One shared fetch of the student's applications, keyed program_id → status.
 * React Query dedupes across every card on the page, so this is a single
 * network call no matter how many cards mount.
 */
export function useAppliedPrograms(): Map<string, AppStatus> {
  const { data } = useQuery({
    queryKey: ['my-applications', 'applied-map'],
    queryFn: listMyApplications,
    staleTime: 60 * 1000,
    retry: false,
  })
  return useMemo(() => {
    const map = new Map<string, AppStatus>()
    for (const a of (data ?? []) as Array<{ program_id?: string; status?: AppStatus }>) {
      if (a?.program_id && a.status && a.status in STAGE) map.set(a.program_id, a.status)
    }
    return map
  }, [data])
}

export default function AppStatusPill({ status }: { status?: AppStatus | null }) {
  if (!status || !(status in STAGE)) return null
  const { label, applied } = STAGE[status]
  const Icon = applied ? CircleCheck : CircleDashed
  return (
    <span
      className={`inline-flex items-center gap-1 px-2 py-0.5 text-[10px] font-semibold rounded-md ${
        applied ? 'bg-secondary/10 text-secondary' : 'bg-muted text-muted-foreground'
      }`}
      title={applied ? `You've applied — ${label.toLowerCase()}` : 'Application started (draft)'}
    >
      <Icon size={10} aria-hidden />
      {label}
    </span>
  )
}
