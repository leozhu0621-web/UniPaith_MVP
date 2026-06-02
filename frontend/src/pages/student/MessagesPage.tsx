import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  getSuggestedReply,
  getThread,
  getThreads,
  markThreadComplete,
  postInboxMessage,
} from '../../api/inbox'
import Skeleton from '../../components/ui/Skeleton'
import type { InboxAttachment, InboxThreadSummary } from '../../types'
import { useMessageStream } from '../../hooks/useMessageStream'
import InboxList, { type InboxFilters } from './inbox/InboxList'
import ThreadView from './inbox/ThreadView'
import { AI_REPLY_LABELS } from './inbox/actionLabels'

// Spec 17 — Inbox. Two-pane: thread list + thread view. Lives at
// /s/manage?tab=messages (+&thread=:id). 30s poll (spec §14).

const DEFAULT_FILTERS: InboxFilters = {
  type: 'all',
  state: 'all',
  application_id: 'all',
  sort: 'urgent',
}

function ThreadSkeleton() {
  return (
    <div className="flex h-full flex-col">
      <div className="border-b border-border px-4 py-3">
        <Skeleton className="mb-2 h-3 w-40" />
        <Skeleton className="h-4 w-56" />
      </div>
      <div className="flex-1 space-y-3 p-6">
        <Skeleton className="h-12 w-2/3" />
        <Skeleton className="ml-auto h-12 w-1/2" />
        <Skeleton className="h-12 w-3/5" />
      </div>
    </div>
  )
}

export default function MessagesPage({ initialThreadId }: { initialThreadId?: string | null }) {
  const navigate = useNavigate()
  const qc = useQueryClient()
  const [selectedId, setSelectedId] = useState<string | null>(initialThreadId || null)
  const [filters, setFilters] = useState<InboxFilters>(DEFAULT_FILTERS)

  // Spec 57 §2 — live WebSocket delivery: a new message patches the thread + list
  // instantly (no poll).
  useMessageStream({ activeThreadId: selectedId })

  const apiFilters = useMemo(
    () => ({
      ...(filters.type !== 'all' ? { type: filters.type } : {}),
      ...(filters.state !== 'all' ? { state: filters.state } : {}),
      ...(filters.application_id !== 'all' ? { application_id: filters.application_id } : {}),
      sort: filters.sort,
    }),
    [filters],
  )

  const { data: threadsData, isLoading: threadsLoading } = useQuery({
    queryKey: ['inbox-threads', apiFilters],
    queryFn: () => getThreads(apiFilters),
    refetchInterval: 30000,
  })
  const threads: InboxThreadSummary[] = useMemo(
    () => (Array.isArray(threadsData) ? threadsData : []),
    [threadsData],
  )

  // Unfiltered list — drives the application-filter options so they don't
  // collapse when a filter is active.
  const { data: allThreadsData } = useQuery({
    queryKey: ['inbox-threads-all'],
    queryFn: () => getThreads({ sort: 'recent' }),
    refetchInterval: 60000,
  })

  const { data: thread, isLoading: threadLoading } = useQuery({
    queryKey: ['inbox-thread', selectedId],
    queryFn: () => getThread(selectedId!),
    enabled: !!selectedId,
    refetchInterval: 30000,
  })

  const aiEligible = !!(thread?.action_label && AI_REPLY_LABELS.includes(thread.action_label))
  const { data: suggestion, isLoading: suggestionLoading } = useQuery({
    queryKey: ['inbox-suggestion', selectedId, thread?.action_label, thread?.messages.length],
    queryFn: () => getSuggestedReply(selectedId!),
    enabled: aiEligible,
    staleTime: Infinity,
    retry: false,
  })

  useEffect(() => {
    if (initialThreadId && initialThreadId !== selectedId) setSelectedId(initialThreadId)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initialThreadId])

  const appOptions = useMemo(() => {
    const all: InboxThreadSummary[] = Array.isArray(allThreadsData) ? allThreadsData : threads
    const seen = new Map<string, string>()
    for (const t of all) {
      if (t.application_id) {
        const label = t.application.program_name || t.application.institution_name || 'Application'
        seen.set(t.application_id, label)
      }
    }
    return [
      { value: 'all', label: 'All applications' },
      ...[...seen].map(([value, label]) => ({ value, label })),
    ]
  }, [allThreadsData, threads])

  const openThread = (id: string) => {
    setSelectedId(id)
    navigate(`/s/manage?tab=messages&thread=${id}`, { replace: true })
  }
  const closeThread = () => {
    setSelectedId(null)
    navigate('/s/manage?tab=messages', { replace: true })
  }

  const sendMut = useMutation({
    mutationFn: ({
      body,
      attachments,
      aiDraftUsed,
    }: {
      body: string
      attachments: InboxAttachment[]
      aiDraftUsed: boolean
    }) => postInboxMessage(selectedId!, { body, attachments, ai_draft_used: aiDraftUsed }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['inbox-thread', selectedId] })
      qc.invalidateQueries({ queryKey: ['inbox-threads'] })
    },
  })

  const completeMut = useMutation({
    mutationFn: () => markThreadComplete(selectedId!),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['inbox-thread', selectedId] })
      qc.invalidateQueries({ queryKey: ['inbox-threads'] })
      // The linked checklist item may now be complete.
      qc.invalidateQueries({ queryKey: ['application-checklist'] })
      qc.invalidateQueries({ queryKey: ['calendar'] })
    },
  })

  return (
    <div className="flex h-full">
      {/* Left: thread list. Mobile (02b §5): list and thread are separate full
          screens — show the list only when no thread is open. */}
      <div
        className={`${selectedId ? 'hidden lg:flex' : 'flex'} w-full flex-col border-r border-border bg-card lg:w-80`}
      >
        <InboxList
          threads={threads}
          loading={threadsLoading}
          selectedId={selectedId}
          onSelect={openThread}
          filters={filters}
          onFilters={setFilters}
          appOptions={appOptions}
        />
      </div>

      {/* Right: thread view. Mobile: full screen when a thread is selected. */}
      <div className={`${selectedId ? 'flex' : 'hidden lg:flex'} flex-1 flex-col`}>
        {!selectedId ? (
          <div className="flex flex-1 items-center justify-center px-6 text-center text-sm text-muted-foreground">
            Pick a conversation to see it here.
          </div>
        ) : threadLoading || !thread ? (
          <ThreadSkeleton />
        ) : (
          <ThreadView
            thread={thread}
            onBack={closeThread}
            onSend={(body, attachments, ai) =>
              sendMut.mutate({ body, attachments, aiDraftUsed: ai })
            }
            sending={sendMut.isPending}
            onMarkComplete={() => completeMut.mutate()}
            completing={completeMut.isPending}
            suggestion={suggestion ?? null}
            suggestionLoading={aiEligible && suggestionLoading}
            onNavigate={navigate}
          />
        )}
      </div>
    </div>
  )
}
