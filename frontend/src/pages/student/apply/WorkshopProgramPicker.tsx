/**
 * General | Program-specific mode selector (Spec/14-workshops.md §2 + §6).
 *
 * In program-specific mode the student picks one of their applications as
 * the target; the panel passes `target_program_id` to the backend and
 * surfaces a per-program readiness summary. The candidate list is the
 * student's own applications (`/applications/me`) — no new endpoint.
 */
import { useQuery } from '@tanstack/react-query'

import { listMyApplications } from '../../../api/applications'

export type WorkshopMode = 'general' | 'program_specific'

export interface ProgramOption {
  programId: string
  programName: string
  institution: string
}

interface Props {
  mode: WorkshopMode
  onModeChange: (m: WorkshopMode) => void
  program: ProgramOption | null
  onProgramChange: (p: ProgramOption | null) => void
}

function normalize(rows: unknown): ProgramOption[] {
  const list = Array.isArray(rows) ? (rows as Record<string, any>[]) : []
  const mapped = list
    .map(a => ({
      programId: a?.program_id ?? a?.program?.id ?? a?.programId ?? '',
      programName:
        a?.program_name ?? a?.program?.name ?? a?.program_title ?? a?.title ?? 'Program',
      institution:
        a?.institution_name ?? a?.institution?.name ?? a?.school_name ?? a?.program?.institution_name ?? '',
    }))
    .filter(o => o.programId)
  // de-dupe by programId
  return Array.from(new Map(mapped.map(o => [o.programId, o] as const)).values())
}

export default function WorkshopProgramPicker({
  mode,
  onModeChange,
  program,
  onProgramChange,
}: Props) {
  const { data, isLoading } = useQuery({
    queryKey: ['workshop-program-options'],
    queryFn: listMyApplications,
    staleTime: 60_000,
  })

  const options = normalize(data)

  const setMode = (m: WorkshopMode) => {
    onModeChange(m)
    if (m === 'general') onProgramChange(null)
    else if (!program) onProgramChange(options[0] ?? null)
  }

  return (
    <div className="space-y-2">
      <div className="inline-flex rounded-lg border border-border p-0.5">
        {(['general', 'program_specific'] as WorkshopMode[]).map(m => (
          <button
            key={m}
            type="button"
            onClick={() => setMode(m)}
            className={`rounded-md px-3 py-1.5 text-sm transition-colors ${
              mode === m
                ? 'bg-primary/10 font-medium text-foreground'
                : 'text-foreground hover:text-foreground'
            }`}
          >
            {m === 'general' ? 'General' : 'Program-specific'}
          </button>
        ))}
      </div>

      {mode === 'program_specific' && (
        <div>
          {isLoading ? (
            <div className="text-xs text-foreground">Loading your programs…</div>
          ) : options.length === 0 ? (
            <div className="text-xs text-foreground">
              Save or start an application to target a specific program — showing general feedback
              for now.
            </div>
          ) : (
            <select
              aria-label="Target program"
              value={program?.programId ?? ''}
              onChange={e => {
                const next = options.find(o => o.programId === e.target.value) ?? null
                onProgramChange(next)
              }}
              className="w-full rounded-md border border-border bg-card px-3 py-2 text-sm text-foreground"
            >
              {options.map(o => (
                <option key={o.programId} value={o.programId}>
                  {o.programName}
                  {o.institution ? ` · ${o.institution}` : ''}
                </option>
              ))}
            </select>
          )}
        </div>
      )}
    </div>
  )
}
