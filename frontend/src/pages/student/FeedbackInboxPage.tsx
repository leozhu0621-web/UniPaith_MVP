import { useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Download, Inbox, Lock, MessageSquarePlus } from 'lucide-react'

import { getFeedbackInbox, type FeedbackItem } from '../../api/feedback'
import { ApiError } from '../../api/client'
import Card from '../../components/ui/Card'
import Button from '../../components/ui/Button'
import QueryError from '../../components/ui/QueryError'
import Skeleton from '../../components/ui/Skeleton'

function pathOf(ctx: FeedbackItem['context']): string | null {
  if (ctx && typeof ctx === 'object' && 'path' in ctx && typeof ctx.path === 'string') {
    return ctx.path
  }
  return null
}

function toCsv(items: FeedbackItem[]): string {
  const esc = (v: string) => `"${v.replace(/"/g, '""')}"`
  const header = ['created_at', 'role', 'title', 'message', 'path']
  const lines = items.map(i =>
    [i.created_at, i.role ?? '', i.title ?? '', i.message, pathOf(i.context) ?? '']
      .map(v => esc(String(v)))
      .join(','),
  )
  return [header.join(','), ...lines].join('\n')
}

function downloadCsv(items: FeedbackItem[]) {
  const blob = new Blob([toCsv(items)], { type: 'text/csv;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'feedback.csv'
  document.body.appendChild(a)
  a.click()
  a.remove()
  URL.revokeObjectURL(url)
}

export default function FeedbackInboxPage() {
  const { data, isLoading, isError, error, refetch } = useQuery<FeedbackItem[]>({
    queryKey: ['feedback-inbox'],
    queryFn: getFeedbackInbox,
    retry: false,
  })

  const items = useMemo(() => data ?? [], [data])
  const forbidden = isError && error instanceof ApiError && error.status === 403

  return (
    <div className="p-4 max-w-5xl w-full mx-auto space-y-4">
      <header className="flex items-end justify-between gap-4">
        <div>
          <p className="text-eyebrow text-accent mb-1">Owner</p>
          <h1 className="text-2xl font-semibold text-foreground">Feedback inbox</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Everything submitted through the in-app Feedback button, newest first.
          </p>
        </div>
        {items.length > 0 && (
          <Button size="sm" variant="secondary" onClick={() => downloadCsv(items)}>
            <Download size={14} className="mr-1.5" /> Export CSV
          </Button>
        )}
      </header>

      {isLoading ? (
        <div className="space-y-3">
          {[1, 2, 3].map(i => (
            <Skeleton key={i} className="h-24" />
          ))}
        </div>
      ) : forbidden ? (
        <Card className="text-center py-16">
          <Lock size={28} className="mx-auto text-muted-foreground mb-3" />
          <p className="text-sm font-medium text-foreground mb-1">This inbox is owner-only</p>
          <p className="text-xs text-muted-foreground max-w-sm mx-auto">
            Your account isn&rsquo;t on the owner allowlist, so you can&rsquo;t read submitted
            feedback. Ask an owner to add your email.
          </p>
        </Card>
      ) : isError ? (
        <QueryError detail="We couldn't load the feedback inbox." onRetry={() => refetch()} />
      ) : items.length === 0 ? (
        <Card className="text-center py-16">
          <Inbox size={28} className="mx-auto text-muted-foreground mb-3" />
          <p className="text-sm font-medium text-foreground mb-1">No feedback yet</p>
          <p className="text-xs text-muted-foreground">
            When someone uses the Feedback button, their note shows up here.
          </p>
        </Card>
      ) : (
        <>
          <p className="text-xs text-muted-foreground">
            {items.length} submission{items.length === 1 ? '' : 's'}
          </p>
          <div className="space-y-3">
            {items.map(item => {
              const path = pathOf(item.context)
              return (
                <Card key={item.id} className="p-4">
                  <div className="flex items-start justify-between gap-3 mb-1.5">
                    <h2 className="text-sm font-semibold text-foreground flex items-center gap-1.5">
                      <MessageSquarePlus size={14} className="text-secondary flex-shrink-0" />
                      {item.title || 'Untitled feedback'}
                    </h2>
                    <time className="text-xs text-muted-foreground whitespace-nowrap">
                      {new Date(item.created_at).toLocaleString()}
                    </time>
                  </div>
                  <p className="text-sm text-foreground whitespace-pre-line leading-relaxed">
                    {item.message}
                  </p>
                  <div className="flex flex-wrap items-center gap-2 mt-3 text-xs text-muted-foreground">
                    {item.role && (
                      <span className="inline-flex items-center rounded-full bg-muted px-2 py-0.5 font-medium">
                        {item.role}
                      </span>
                    )}
                    {path && (
                      <span>
                        from <span className="font-mono text-foreground/80">{path}</span>
                      </span>
                    )}
                  </div>
                </Card>
              )
            })}
          </div>
        </>
      )}
    </div>
  )
}
