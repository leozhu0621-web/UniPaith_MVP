// Spec 57 §5 — the notification center bell.
//
// Live unread badge (SSE-patched, no poll), a grouped panel with mark-one /
// mark-all-read, deep-links to the source, and a scrollable recent history. The
// stream is opened by useNotificationStream(); read-state syncs across tabs and
// devices because the backend echoes read events to every open stream.

import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Bell, CheckCheck, Inbox } from 'lucide-react'

import { getNotifications, getUnreadCount, markAllRead, markRead } from '../../api/notifications'
import { qk } from '../../api/queryKeys'
import { useNotificationStream } from '../../hooks/useNotificationStream'
import { formatRelative } from '../../utils/format'
import type { Notification } from '../../types'

export default function NotificationBell() {
  const [open, setOpen] = useState(false)
  const wrapRef = useRef<HTMLDivElement>(null)
  const navigate = useNavigate()
  const qc = useQueryClient()

  // Open the live SSE stream; it patches the unread-count + list caches.
  useNotificationStream()

  const { data: unread } = useQuery({
    queryKey: qk.notificationsUnread(),
    queryFn: getUnreadCount,
    staleTime: 30_000,
  })
  const count: number = unread?.count ?? 0

  const { data: items, isLoading } = useQuery<Notification[]>({
    queryKey: qk.notifications(),
    queryFn: () => getNotifications({ limit: 20 }),
    enabled: open, // only fetch the history when the panel is opened
    staleTime: 15_000,
  })

  const markOne = useMutation({
    mutationFn: (id: string) => markRead(id),
    onSuccess: (_d, id) =>
      qc.setQueryData<Notification[] | undefined>(qk.notifications(), (old) =>
        Array.isArray(old) ? old.map((n) => (n.id === id ? { ...n, is_read: true } : n)) : old,
      ),
  })

  const markAll = useMutation({
    mutationFn: () => markAllRead(),
    onSuccess: () => {
      qc.setQueryData<Notification[] | undefined>(qk.notifications(), (old) =>
        Array.isArray(old) ? old.map((n) => ({ ...n, is_read: true })) : old,
      )
      qc.setQueryData(qk.notificationsUnread(), { count: 0 })
    },
  })

  useEffect(() => {
    if (!open) return
    const onClick = (e: MouseEvent) => {
      if (wrapRef.current && !wrapRef.current.contains(e.target as Node)) setOpen(false)
    }
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setOpen(false)
    }
    document.addEventListener('mousedown', onClick)
    document.addEventListener('keydown', onKey)
    return () => {
      document.removeEventListener('mousedown', onClick)
      document.removeEventListener('keydown', onKey)
    }
  }, [open])

  const onItemClick = (n: Notification) => {
    if (!n.is_read) markOne.mutate(n.id)
    setOpen(false)
    if (n.action_url) navigate(n.action_url)
  }

  const list = items ?? []

  return (
    <div ref={wrapRef} className="relative">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-label={count ? `Notifications, ${count} unread` : 'Notifications'}
        aria-expanded={open}
        className="ui-btn relative p-2 rounded-lg hover:bg-muted text-muted-foreground hover:text-foreground transition-colors"
      >
        <Bell size={19} />
        {count > 0 && (
          <span className="absolute -right-0.5 -top-0.5 inline-flex h-[18px] min-w-[18px] items-center justify-center rounded-full bg-secondary px-1 text-[10px] font-semibold leading-none text-secondary-foreground">
            {count > 9 ? '9+' : count}
          </span>
        )}
      </button>

      {open && (
        <div
          role="dialog"
          aria-label="Notifications"
          className="absolute right-0 top-[calc(100%+8px)] z-50 w-[min(360px,calc(100vw-2rem))] overflow-hidden rounded-lg border border-border bg-card text-foreground elev-raised animate-slide-up-fade"
        >
          <div className="flex items-center justify-between border-b border-border px-4 py-3">
            <span className="text-h3 text-foreground">Notifications</span>
            {count > 0 && (
              <button
                type="button"
                onClick={() => markAll.mutate()}
                disabled={markAll.isPending}
                className="inline-flex items-center gap-1 text-[12px] font-semibold text-secondary hover:underline disabled:opacity-50"
              >
                <CheckCheck size={13} /> Mark all read
              </button>
            )}
          </div>

          <div className="max-h-[min(70vh,420px)] overflow-y-auto">
            {isLoading ? (
              [0, 1, 2].map((i) => (
                <div key={i} className="border-b border-border px-4 py-3">
                  <div className="h-4 w-2/3 animate-pulse rounded bg-muted" />
                  <div className="mt-2 h-3 w-full animate-pulse rounded bg-muted" />
                </div>
              ))
            ) : list.length === 0 ? (
              <div className="px-4 py-10 text-center">
                <Inbox size={24} className="mx-auto text-muted-foreground" />
                <p className="mt-2 text-sm text-muted-foreground">You&apos;re all caught up.</p>
              </div>
            ) : (
              list.map((n) => (
                <button
                  key={n.id}
                  type="button"
                  onClick={() => onItemClick(n)}
                  className={`block w-full border-b border-border px-4 py-3 text-left transition-colors last:border-0 hover:bg-muted ${
                    n.is_read ? '' : 'bg-secondary/5'
                  }`}
                >
                  <div className="flex items-start gap-2.5">
                    <span
                      className={`mt-1.5 h-2 w-2 shrink-0 rounded-full ${
                        n.is_read ? 'bg-transparent' : 'bg-secondary'
                      }`}
                      aria-hidden
                    />
                    <div className="min-w-0 flex-1">
                      <p
                        className={`text-sm leading-snug ${
                          n.is_read ? 'text-muted-foreground' : 'font-semibold text-foreground'
                        }`}
                      >
                        {n.title}
                      </p>
                      <p className="mt-0.5 line-clamp-2 text-[13px] text-muted-foreground">
                        {n.body}
                      </p>
                      <p className="mt-1 text-[11px] text-muted-foreground">
                        {formatRelative(n.created_at)}
                      </p>
                    </div>
                  </div>
                </button>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  )
}
