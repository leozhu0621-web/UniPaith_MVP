/**
 * Apply → Prompts sub-tab (Spec 42 §3.19–§3.20 / §4.17).
 *
 * The Prompt Library: a catalog of ~60 canonical behavioral prompts the student
 * answers once and reuses across interviews and essays, plus a Story Bank of
 * reusable narrative units. STAR completeness is auto-detected; an interview-
 * readiness signal + competency coverage come from the PromptCoach overlay.
 *
 * Distinct from Workshops (which give feedback on a finished draft) — this is the
 * durable practice layer. Feedback-only ethos throughout: we coach structure and
 * surface gaps; we never write the answer.
 */
import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { MessagesSquare, Search } from 'lucide-react'

import {
  getSummary,
  listPrompts,
  listResponses,
  listStories,
} from '../../../../api/prompt-library'
import Card from '../../../../components/ui/Card'
import type { BehavioralPrompt } from '../../../../types/promptLibrary'

import { CHANNEL_LABELS, INTENT_LABELS } from './constants'
import PromptCard from './PromptCard'
import ReadinessHeader from './ReadinessHeader'
import ResponseEditor from './ResponseEditor'
import StoryBankPanel from './StoryBankPanel'

type StatusFilter = 'all' | 'unanswered' | 'in_progress' | 'final'

export default function PromptLibraryTab() {
  const prompts = useQuery({ queryKey: ['prompt-library', 'prompts'], queryFn: () => listPrompts() })
  const responses = useQuery({ queryKey: ['prompt-library', 'responses'], queryFn: listResponses })
  const stories = useQuery({ queryKey: ['prompt-library', 'stories'], queryFn: listStories })
  const summary = useQuery({ queryKey: ['prompt-library', 'summary'], queryFn: getSummary })

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
    <div className="mx-auto max-w-5xl space-y-5 p-6">
      <header>
        <h2 className="flex items-center gap-2 text-h3 text-foreground">
          <MessagesSquare size={20} /> Prompt Library
        </h2>
        <p className="mt-1 text-sm text-muted-foreground">
          Answer the questions admissions and interviewers actually ask — once — then reuse your
          best stories everywhere. We coach structure and flag gaps; we never write your answer.
        </p>
      </header>

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
            <Card variant="card-flush" className="px-4 py-10 text-center text-sm text-muted-foreground">
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
    </div>
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
