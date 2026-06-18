// "Application season" overview (Discover review 2026-06-14 #4) — promotes the
// cramped deadline radar into a horizontal month strip of upcoming program
// deadlines, with a per-month batch "Remind me" (Handshake deadline tracker).
// Self-hides when there are no upcoming deadlines. Cobalt/neutral, no gold.
import { useNavigate } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { CalendarClock, BellPlus } from 'lucide-react'
import { getConnectFeed, type ConnectFeedItem } from '../../../api/connect'
import { createReminder } from '../../../api/calendar'
import { showToast } from '../../../stores/toast-store'
import { groupByMonth } from './seasonGroups'

function urgencyText(soonest: number): string {
  return soonest <= 7 ? 'text-error' : soonest <= 30 ? 'text-warning' : 'text-muted-foreground'
}

export default function ApplicationSeason() {
  const navigate = useNavigate()
  const qc = useQueryClient()
  const { data } = useQuery({
    queryKey: ['connect-deadline-radar'],
    queryFn: () => getConnectFeed('recent', undefined, { limit: 40, kinds: 'deadline' }),
    staleTime: 5 * 60 * 1000,
    retry: false,
  })

  const remindAll = useMutation({
    mutationFn: async (items: ConnectFeedItem[]) => {
      // Best-effort batch — one reminder per program deadline in the month.
      await Promise.allSettled(
        items
          .filter(it => it.deadline)
          .map(it =>
            createReminder({
              title: `${it.program_name || 'Program'} — application deadline`,
              start_at: new Date(it.deadline as string).toISOString(),
              notes: it.institution_name ? `From ${it.institution_name}` : null,
            }),
          ),
      )
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['calendar'] })
      showToast('Reminders added for the month', 'success')
    },
    onError: () => showToast("We couldn't add those reminders. Please try again.", 'error'),
  })

  const months = groupByMonth(data?.items ?? [])
  if (months.length === 0) return null

  return (
    <section className="mb-4 rounded-xl border border-border bg-card p-4" aria-label="Application season">
      <div className="flex items-center gap-2 mb-3">
        <CalendarClock size={14} className="text-secondary" aria-hidden />
        <h2 className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">Application season</h2>
      </div>

      <div className="flex gap-3 overflow-x-auto no-scrollbar pb-1">
        {months.map(m => (
          <div key={m.key} className="min-w-[10rem] flex-shrink-0 rounded-lg border border-border bg-muted/30 p-3">
            <div className="flex items-baseline justify-between gap-2">
              <span className="text-sm font-semibold text-foreground">{m.label}</span>
              <span className={`text-xs font-medium ${urgencyText(m.soonest)}`}>
                {m.count} due
              </span>
            </div>
            <div className="mt-2 space-y-1">
              {m.items.slice(0, 3).map(it => (
                <button
                  key={it.id}
                  onClick={() => (it.program_id ? navigate(`/s/programs/${it.program_id}`) : undefined)}
                  className="block w-full truncate text-left text-xs text-muted-foreground hover:text-foreground"
                  title={it.program_name ?? undefined}
                >
                  {it.program_name}
                </button>
              ))}
              {m.count > 3 && <p className="text-[10px] text-muted-foreground/70">+{m.count - 3} more</p>}
            </div>
            <button
              onClick={() => remindAll.mutate(m.items)}
              disabled={remindAll.isPending}
              className="mt-2 inline-flex items-center gap-1 text-[11px] font-semibold text-secondary hover:underline disabled:opacity-50"
            >
              <BellPlus size={11} /> Remind me
            </button>
          </div>
        ))}
      </div>
    </section>
  )
}
