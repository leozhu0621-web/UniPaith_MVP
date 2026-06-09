import { Calendar, CalendarPlus } from 'lucide-react'
import type { InstitutionPost } from '../types'
import { addEventToCalendar } from '../api/events'
import { showToast } from '../stores/toast-store'

/** Host of a source URL, for "via {host}" channel attribution. */
function hostOf(url?: string | null): string | null {
  if (!url) return null
  try {
    return new URL(url).hostname.replace(/^www\./, '')
  } catch {
    return null
  }
}

function fmtDate(d?: string | null): string | null {
  if (!d) return null
  const dt = new Date(d)
  if (Number.isNaN(dt.getTime())) return null
  return dt.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

type GridItem =
  | {
      kind: 'post'
      key: string
      title: string
      dek: string
      url: string | null
      host: string | null
      image: string | null
      date: string | null
      ts: number
    }
  | {
      kind: 'event'
      key: string
      eventId: string
      eventName: string
      title: string
      location: string | null
      url: string | null
      host: string | null
      date: string | null
      ts: number
    }

/**
 * News-magazine grid for Events & Updates (institution / school / program).
 * Updates render the real source image; events render a gradient + date card
 * (no source image exists). Items are merged + sorted newest-first.
 */
export default function NewsGrid({
  posts = [],
  events = [],
  emptyText = 'Nothing published yet.',
}: {
  posts?: InstitutionPost[]
  events?: any[]
  emptyText?: string
}) {
  const items: GridItem[] = []

  for (const p of posts) {
    const date = p.published_at || p.created_at
    items.push({
      kind: 'post',
      key: `post-${p.id}`,
      title: p.title,
      dek: p.body || '',
      url: p.source_url ?? null,
      host: p.source && p.source !== 'manual' ? hostOf(p.source_url) : null,
      image: p.image_url ?? null,
      date: fmtDate(date),
      ts: date ? new Date(date).getTime() : 0,
    })
  }
  for (const e of events) {
    items.push({
      kind: 'event',
      key: `event-${e.id}`,
      eventId: e.id,
      eventName: e.event_name,
      title: e.event_name,
      location: e.location ?? null,
      url: e.source_url ?? null,
      host: e.source && e.source !== 'manual' ? hostOf(e.source_url) : null,
      date: fmtDate(e.start_time),
      ts: e.start_time ? new Date(e.start_time).getTime() : 0,
    })
  }
  items.sort((a, b) => b.ts - a.ts)

  if (items.length === 0) {
    return <p className="text-sm text-muted-foreground">{emptyText}</p>
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
      {items.map(it =>
        it.kind === 'post' ? (
          <a
            key={it.key}
            href={it.url ?? undefined}
            target={it.url ? '_blank' : undefined}
            rel="noopener noreferrer"
            className="group block bg-card rounded-xl border border-border overflow-hidden hover:shadow-sm transition-shadow"
          >
            {it.image ? (
              <div className="aspect-[16/9] bg-muted overflow-hidden">
                <img
                  src={it.image}
                  alt=""
                  loading="lazy"
                  className="w-full h-full object-cover group-hover:scale-[1.02] transition-transform"
                />
              </div>
            ) : (
              <div className="aspect-[16/9] bg-gradient-to-br from-secondary/15 to-muted" />
            )}
            <div className="p-4">
              <h3 className="text-sm font-semibold text-foreground line-clamp-2 group-hover:text-secondary">
                {it.title}
              </h3>
              {it.dek && <p className="text-xs text-muted-foreground line-clamp-2 mt-1">{it.dek}</p>}
              <div className="flex items-center gap-2 mt-2 text-[11px] text-muted-foreground">
                {it.host && <span className="text-secondary">via {it.host} ↗</span>}
                {it.date && <span className="ml-auto">{it.date}</span>}
              </div>
            </div>
          </a>
        ) : (
          <div key={it.key} className="bg-card rounded-xl border border-border overflow-hidden">
            <div className="aspect-[16/9] bg-gradient-to-br from-secondary/15 to-muted flex flex-col items-center justify-center">
              <Calendar size={24} className="text-secondary" />
              {it.date && <span className="mt-1.5 text-xs font-semibold text-foreground">{it.date}</span>}
            </div>
            <div className="p-4">
              <h3 className="text-sm font-semibold text-foreground line-clamp-2">{it.title}</h3>
              {it.location && (
                <p className="text-xs text-muted-foreground line-clamp-1 mt-1">{it.location}</p>
              )}
              <div className="flex items-center gap-3 mt-2 text-[11px]">
                <button
                  onClick={() =>
                    addEventToCalendar(it.eventId, it.eventName).catch(() =>
                      showToast('Couldn’t generate the calendar file.', 'error'),
                    )
                  }
                  className="inline-flex items-center gap-1 text-secondary hover:underline"
                >
                  <CalendarPlus size={11} /> Add to calendar
                </button>
                {it.host && it.url && (
                  <a
                    href={it.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-muted-foreground hover:text-secondary hover:underline ml-auto"
                  >
                    via {it.host} ↗
                  </a>
                )}
              </div>
            </div>
          </div>
        ),
      )}
    </div>
  )
}
