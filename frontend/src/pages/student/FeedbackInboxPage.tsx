import { useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Download, Inbox, Lock, MessageSquarePlus } from 'lucide-react'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Legend,
} from 'recharts'

import { getFeedbackInbox, type FeedbackItem } from '../../api/feedback'
import { ApiError } from '../../api/client'
import Card from '../../components/ui/Card'
import Button from '../../components/ui/Button'
import QueryError from '../../components/ui/QueryError'
import Skeleton from '../../components/ui/Skeleton'

const ROLE_COLORS: Record<string, string> = {
  student: '#6366f1',
  institution_admin: '#10b981',
  admin: '#f59e0b',
  unknown: '#94a3b8',
}

const BAR_COLOR = '#6366f1'

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

function useChartData(items: FeedbackItem[]) {
  return useMemo(() => {
    // --- Submissions over time (by day) ---
    const dayCounts: Record<string, number> = {}
    for (const item of items) {
      const day = item.created_at.slice(0, 10) // YYYY-MM-DD
      dayCounts[day] = (dayCounts[day] ?? 0) + 1
    }
    const byDay = Object.entries(dayCounts)
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([day, count]) => ({
        day: day.slice(5), // MM-DD for display
        count,
      }))

    // --- By role ---
    const roleCounts: Record<string, number> = {}
    for (const item of items) {
      const role = item.role ?? 'unknown'
      roleCounts[role] = (roleCounts[role] ?? 0) + 1
    }
    const byRole = Object.entries(roleCounts)
      .sort(([, a], [, b]) => b - a)
      .map(([name, value]) => ({ name, value }))

    // --- Top pages ---
    const pageCounts: Record<string, number> = {}
    for (const item of items) {
      const p = pathOf(item.context) ?? '(no path)'
      pageCounts[p] = (pageCounts[p] ?? 0) + 1
    }
    const byPage = Object.entries(pageCounts)
      .sort(([, a], [, b]) => b - a)
      .slice(0, 10)
      .map(([page, count]) => ({ page, count }))

    return { byDay, byRole, byPage }
  }, [items])
}

export default function FeedbackInboxPage() {
  const { data, isLoading, isError, error, refetch } = useQuery<FeedbackItem[]>({
    queryKey: ['feedback-inbox'],
    queryFn: getFeedbackInbox,
    retry: false,
  })

  const items = useMemo(() => data ?? [], [data])
  const forbidden = isError && error instanceof ApiError && error.status === 403
  const { byDay, byRole, byPage } = useChartData(items)

  return (
    <div className="p-4 w-full space-y-6">
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
          {/* ── Charts ── */}
          <section className="space-y-3">
            <h2 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
              Overview — {items.length} submission{items.length === 1 ? '' : 's'}
            </h2>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
              {/* Submissions over time */}
              <Card className="p-4 col-span-1 lg:col-span-2">
                <p className="text-xs font-medium text-muted-foreground mb-3">Submissions over time</p>
                <ResponsiveContainer width="100%" height={180}>
                  <BarChart data={byDay} margin={{ top: 4, right: 8, left: -20, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                    <XAxis
                      dataKey="day"
                      tick={{ fontSize: 10, fill: 'var(--muted-foreground)' }}
                      tickLine={false}
                      axisLine={false}
                    />
                    <YAxis
                      allowDecimals={false}
                      tick={{ fontSize: 10, fill: 'var(--muted-foreground)' }}
                      tickLine={false}
                      axisLine={false}
                    />
                    <Tooltip
                      contentStyle={{
                        background: 'var(--card)',
                        border: '1px solid var(--border)',
                        borderRadius: 6,
                        fontSize: 12,
                      }}
                      cursor={{ fill: 'var(--muted)', opacity: 0.4 }}
                    />
                    <Bar dataKey="count" fill={BAR_COLOR} radius={[3, 3, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </Card>

              {/* By role */}
              <Card className="p-4">
                <p className="text-xs font-medium text-muted-foreground mb-3">By role</p>
                <ResponsiveContainer width="100%" height={180}>
                  <PieChart>
                    <Pie
                      data={byRole}
                      dataKey="value"
                      nameKey="name"
                      cx="50%"
                      cy="45%"
                      innerRadius={40}
                      outerRadius={65}
                      paddingAngle={2}
                    >
                      {byRole.map(entry => (
                        <Cell
                          key={entry.name}
                          fill={ROLE_COLORS[entry.name] ?? ROLE_COLORS.unknown}
                        />
                      ))}
                    </Pie>
                    <Tooltip
                      contentStyle={{
                        background: 'var(--card)',
                        border: '1px solid var(--border)',
                        borderRadius: 6,
                        fontSize: 12,
                      }}
                    />
                    <Legend
                      iconType="circle"
                      iconSize={8}
                      wrapperStyle={{ fontSize: 11 }}
                    />
                  </PieChart>
                </ResponsiveContainer>
              </Card>
            </div>

            {/* Top pages */}
            {byPage.length > 0 && (
              <Card className="p-4">
                <p className="text-xs font-medium text-muted-foreground mb-3">Top pages</p>
                <ResponsiveContainer width="100%" height={Math.max(120, byPage.length * 28)}>
                  <BarChart
                    data={byPage}
                    layout="vertical"
                    margin={{ top: 0, right: 16, left: 8, bottom: 0 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" horizontal={false} />
                    <XAxis
                      type="number"
                      allowDecimals={false}
                      tick={{ fontSize: 10, fill: 'var(--muted-foreground)' }}
                      tickLine={false}
                      axisLine={false}
                    />
                    <YAxis
                      type="category"
                      dataKey="page"
                      width={180}
                      tick={{ fontSize: 10, fill: 'var(--muted-foreground)', fontFamily: 'monospace' }}
                      tickLine={false}
                      axisLine={false}
                    />
                    <Tooltip
                      contentStyle={{
                        background: 'var(--card)',
                        border: '1px solid var(--border)',
                        borderRadius: 6,
                        fontSize: 12,
                      }}
                      cursor={{ fill: 'var(--muted)', opacity: 0.4 }}
                    />
                    <Bar dataKey="count" fill={BAR_COLOR} radius={[0, 3, 3, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </Card>
            )}
          </section>

          {/* ── Full list ── */}
          <section className="space-y-3">
            <h2 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
              All submissions
            </h2>
            {items.map(item => {
              const path = pathOf(item.context)
              return (
                <Card key={item.id} className="p-4">
                  <div className="flex items-start justify-between gap-3 mb-1.5">
                    <h3 className="text-sm font-semibold text-foreground flex items-center gap-1.5">
                      <MessageSquarePlus size={14} className="text-secondary flex-shrink-0" />
                      {item.title || 'Untitled feedback'}
                    </h3>
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
          </section>
        </>
      )}
    </div>
  )
}
