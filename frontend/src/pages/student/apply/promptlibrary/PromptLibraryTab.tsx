/**
 * Apply → Prompts sub-tab (Spec 42 §3.19–§3.20 / §4.17 + Spec 43 §3.18 / §4.18).
 *
 * Two companion practice layers under one tab, switched by a segmented control:
 *  • Behavioral practice (Spec 42) — a catalog of canonical behavioral prompts
 *    the student answers once and reuses, plus a Story Bank; STAR is auto-
 *    detected and an interview-readiness signal comes from PromptCoach.
 *  • Major-specific readiness (Spec 43) — per-discipline self-ratings that yield
 *    a fit score, coverage map, and suggested artifacts from MajorTrackCoach.
 *
 * Both are distinct from Workshops (which give feedback on a finished draft).
 * Feedback-only ethos throughout: we coach structure and surface gaps; we never
 * write the answer or fill the field.
 */
import { type ReactNode, useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useSearchParams } from 'react-router-dom'
import { Compass, MessagesSquare, Search } from 'lucide-react'
import clsx from 'clsx'

import {
  getSummary,
  listPrompts,
  listResponses,
  listStories,
} from '../../../../api/prompt-library'
import Card from '../../../../components/ui/Card'
import type { BehavioralPrompt } from '../../../../types/promptLibrary'

import MajorSpecificPanel from '../majorspecific/MajorSpecificPanel'
import { CHANNEL_LABELS, INTENT_LABELS } from './constants'
import PromptCard from './PromptCard'
import ReadinessHeader from './ReadinessHeader'
import ResponseEditor from './ResponseEditor'
import StoryBankPanel from './StoryBankPanel'

type StatusFilter = 'all' | 'unanswered' | 'in_progress' | 'final'
type View = 'behavioral' | 'major'

export default function PromptLibraryTab() {
  const [searchParams, setSearchParams] = useSearchParams()
  const view: View = searchParams.get('view') === 'major' ? 'major' : 'behavioral'
  const setView = (v: View) => {
    const next = new URLSearchParams(searchParams)
    if (v === 'major') next.set('view', 'major')
    else next.delete('view')
    setSearchParams(next, { replace: true })
  }

  const behavioral = view === 'behavioral'
  const prompts = useQuery({
    queryKey: ['prompt-library', 'prompts'],
    queryFn: () => listPrompts(),
    enabled: behavioral,
  })
  const responses = useQuery({
    queryKey: ['prompt-library', 'responses'],
    queryFn: listResponses,
    enabled: behavioral,
  })
  const stories = useQuery({
    queryKey: ['prompt-library', 'stories'],
    queryFn: listStories,
    enabled: behavioral,
  })
  const summary = useQuery({
    queryKey: ['prompt-library', 'summary'],
    queryFn: getSummary,
    enabled: behavioral,
  })

  const [q, setQ] = useState('')
  const [intent, setIntent] = useState('')
  const [channel, setChannel] = useState('')
  const [statusF, setStatusF] = useState<StatusFilter>('all')
  const [editing, setEditing] = useState<BehavioralPrompt | null>(null)
  const [open, setOpen] = useState(false)

  const respByKey = useMemo(() => {
    const m = new Map(responses.data?.map(r => [r.prompt_key, r]))
    return m
  }, [responses.data])

  const intents = useMemo(() => {
    const set = new Set((prompts.data ?? []).map(p => p.intent_tag))
    return [...set]
  }, [prompts.data])

  const filtered = useMemo(() => {
    const ql = q.trim().toLowerCase()
    return (prompts.data ?? []).filter(p => {
      if (intent && p.intent_tag !== intent) return false
      if (channel && p.target_channel !== channel) return false
      if (ql && !p.title.toLowerCase().includes(ql)) return false
      const r = respByKey.get(p.prompt_key)
      const answered = !!(r && (r.response_text ?? '').trim())
      if (statusF === 'unanswered' && answered) return false
      if (statusF === 'in_progress' && !(r && ['draft', 'revised'].includes(r.draft_status)))
        return false
      if (statusF === 'final' && r?.draft_status !== 'final') return false
      return true
    })
  }, [prompts.data, q, intent, channel, statusF, respByKey])

  const grouped = useMemo(() => {
    const g = new Map<string, BehavioralPrompt[]>()
    for (const p of filtered) {
      const arr = g.get(p.intent_tag) ?? []
      arr.push(p)
      g.set(p.intent_tag, arr)
    }
    return [...g.entries()]
  }, [filtered])

  const openEditor = (p: BehavioralPrompt) => {
    setEditing(p)
    setOpen(true)
  }

  const isLoading = prompts.isLoading || responses.isLoading || summary.isLoading
  const isError = prompts.isError

  return (
    <div className="w-full space-y-5 p-6">
      <header>
        <h2 className="flex items-center gap-2 text-h3 text-foreground">
          <MessagesSquare size={20} /> Prompt Library
        </h2>
        <p className="mt-1 text-sm text-muted-foreground">
          Practice the questions admissions and interviewers actually ask, and assess your readiness
          in your target field. We coach structure and flag gaps; we never write your answer.
        </p>
      </header>

      {/* View toggle — behavioral practice (Spec 42) vs major-specific (Spec 43). */}
      <div className="inline-flex rounded-lg border border-border bg-muted p-0.5" role="tablist">
        <ViewTab
          active={view === 'behavioral'}
          onClick={() => setView('behavioral')}
          icon={<MessagesSquare size={15} />}
          label="Behavioral practice"
        />
        <ViewTab
          active={view === 'major'}
          onClick={() => setView('major')}
          icon={<Compass size={15} />}
          label="Major-specific readiness"
        />
      </div>

      {view === 'major' ? (
        <MajorSpecificPanel />
      ) : (
        <>
          {isError && (
            <Card className="text-sm text-foreground">
              We couldn&apos;t load the prompt library just now. Please refresh in a moment.
            </Card>
          )}

          {isLoading ? (
            <LoadingSkeleton />
          ) : (
            <>
              {summary.data && <ReadinessHeader summary={summary.data} />}

              {/* Filters */}
              <div className="flex flex-wrap items-center gap-2">
                <div className="relative min-w-[180px] flex-1">
                  <Search
                    size={15}
                    className="pointer-events-none absolute left-2.5 top-1/2 -translate-y-1/2 text-muted-foreground"
                  />
                  <input
                    value={q}
                    onChange={e => setQ(e.target.value)}
                    placeholder="Search prompts…"
                    className="w-full rounded-md border border-border bg-background py-2 pl-8 pr-3 text-sm text-foreground focus:border-secondary focus:outline-none"
                  />
                </div>
                <select
                  value={intent}
                  onChange={e => setIntent(e.target.value)}
                  className="rounded-md border border-border bg-background px-3 py-2 text-sm text-foreground focus:border-secondary focus:outline-none"
                >
                  <option value="">All themes</option>
                  {intents.map(i => (
                    <option key={i} value={i}>
                      {INTENT_LABELS[i] ?? i}
                    </option>
                  ))}
                </select>
                <select
                  value={channel}
                  onChange={e => setChannel(e.target.value)}
                  className="rounded-md border border-border bg-background px-3 py-2 text-sm text-foreground focus:border-secondary focus:outline-none"
                >
                  <option value="">All formats</option>
                  {Object.entries(CHANNEL_LABELS).map(([k, v]) => (
                    <option key={k} value={k}>
                      {v}
                    </option>
                  ))}
                </select>
                <select
                  value={statusF}
                  onChange={e => setStatusF(e.target.value as StatusFilter)}
                  className="rounded-md border border-border bg-background px-3 py-2 text-sm text-foreground focus:border-secondary focus:outline-none"
                >
                  <option value="all">All</option>
                  <option value="unanswered">Unanswered</option>
                  <option value="in_progress">In progress</option>
                  <option value="final">Final</option>
                </select>
              </div>

              {/* Catalog grouped by theme */}
              {grouped.length === 0 ? (
                <Card pad={false}
                  variant="card-flush"
                  className="px-4 py-10 text-center text-sm text-muted-foreground"
                >
                  No prompts match these filters.
                </Card>
              ) : (
                <div className="space-y-6">
                  {grouped.map(([tag, items]) => (
                    <section key={tag}>
                      <h3 className="mb-2 text-eyebrow uppercase tracking-wide text-muted-foreground">
                        {INTENT_LABELS[tag] ?? tag}
                        <span className="ml-1.5 text-muted-foreground/60">{items.length}</span>
                      </h3>
                      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
                        {items.map(p => (
                          <PromptCard
                            key={p.prompt_key}
                            prompt={p}
                            response={respByKey.get(p.prompt_key)}
                            onEdit={openEditor}
                          />
                        ))}
                      </div>
                    </section>
                  ))}
                </div>
              )}

              <div className="border-t border-border pt-5">
                <StoryBankPanel stories={stories.data ?? []} />
              </div>
            </>
          )}

          <ResponseEditor
            prompt={editing}
            response={editing ? respByKey.get(editing.prompt_key) : undefined}
            stories={stories.data ?? []}
            isOpen={open}
            onClose={() => setOpen(false)}
          />
        </>
      )}
    </div>
  )
}

function ViewTab({
  active,
  onClick,
  icon,
  label,
}: {
  active: boolean
  onClick: () => void
  icon: ReactNode
  label: string
}) {
  return (
    <button
      type="button"
      role="tab"
      aria-selected={active}
      onClick={onClick}
      className={clsx(
        'inline-flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm font-medium transition-colors',
        active
          ? 'bg-background text-foreground shadow-sm'
          : 'text-muted-foreground hover:text-foreground',
      )}
    >
      {icon}
      {label}
    </button>
  )
}

function LoadingSkeleton() {
  return (
    <div className="space-y-4">
      <div className="h-28 animate-pulse rounded-xl bg-muted" />
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="h-28 animate-pulse rounded-xl bg-muted" />
        ))}
      </div>
    </div>
  )
}
