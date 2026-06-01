import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Users } from 'lucide-react'
import {
  assignInstInboxThread,
  closeInstInboxThread,
  getInstInboxAiDraft,
  getInstInboxThread,
  getInstInboxThreads,
  postInstBulkMessage,
  postInstInboxMessage,
} from '../../api/institutionInbox'
import { getInstitutionPrograms } from '../../api/institutions'
import Button from '../../components/ui/Button'
import EmptyState from '../../components/ui/EmptyState'
import Skeleton from '../../components/ui/Skeleton'
import { showToast } from '../../stores/toast-store'
import type { InstInboxThreadSummary, InstReasonCode } from '../../types'
import ApplicantContextPanel from './inbox/ApplicantContextPanel'
import BulkMessageModal from './inbox/BulkMessageModal'
import InstInboxList, { type InstListFilters } from './inbox/InstInboxList'
import InstThreadView from './inbox/InstThreadView'

const DEFAULT_FILTERS: InstListFilters = {
  filter: 'all',
  reason: 'all',
  program_id: 'all',
}

export default function InstitutionInboxPage() {
  const navigate = useNavigate()
  const qc = useQueryClient()
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [filters, setFilters] = useState<InstListFilters>(DEFAULT_FILTERS)
  const [bulkOpen, setBulkOpen] = useState(false)

  const apiFilters = useMemo(
    () => ({
      filter: filters.filter,
      ...(filters.reason !== 'all' ? { reason: filters.reason } : {}),
      ...(filters.program_id !== 'all' ? { program_id: filters.program_id } : {}),
    }),
    [filters],
  )

  const { data: threadsData, isLoading: threadsLoading } = useQuery({
    queryKey: ['inst-inbox-threads', apiFilters],
    queryFn: () => getInstInboxThreads(apiFilters),
    refetchInterval: 30000,
  })
  const threads: InstInboxThreadSummary[] = useMemo(
    () => (Array.isArray(threadsData) ? threadsData : []),
    [threadsData],
  )

  const { data: allThreadsData } = useQuery({
    queryKey: ['inst-inbox-threads-all'],
    queryFn: () => getInstInboxThreads({ filter: 'all' }),
    refetchInterval: 60000,
  })
  const unassignedCount = useMemo(
    () =>
      (Array.isArray(allThreadsData) ? allThreadsData : []).filter(
        t => !t.assigned_to && t.status === 'awaiting_us',
      ).length,
    [allThreadsData],
  )

  const programsQ = useQuery({ queryKey: ['institution-programs'], queryFn: getInstitutionPrograms })
  const programOptions = useMemo(
    () =>
      (Array.isArray(programsQ.data) ? programsQ.data : []).map(p => ({
        value: p.id,
        label: p.program_name,
      })),
    [programsQ.data],
  )

  const { data: thread, isLoading: threadLoading } = useQuery({
    queryKey: ['inst-inbox-thread', selectedId],
    queryFn: () => getInstInboxThread(selectedId!),
    enabled: !!selectedId,
  })

  const { data: suggestion, isLoading: suggestionLoading, refetch: refetchSuggestion } = useQuery({
    queryKey: ['inst-inbox-suggestion', selectedId],
    queryFn: () => getInstInboxAiDraft(selectedId!),
    enabled: false,
  })

  const sendMut = useMutation({
    mutationFn: ({
      body,
      reason,
      dueDate,
      aiUsed,
    }: {
      body: string
      reason: InstReasonCode
      dueDate: string | null
      aiUsed: boolean
    }) =>
      postInstInboxMessage(selectedId!, {
        body,
        reason_code: reason,
        due_date: dueDate || undefined,
        ai_draft_used: aiUsed,
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['inst-inbox-thread', selectedId] })
      qc.invalidateQueries({ queryKey: ['inst-inbox-threads'] })
      showToast('Message sent', 'success')
    },
    onError: () => showToast('Failed to send message', 'error'),
  })

  const assignMut = useMutation({
    mutationFn: () => assignInstInboxThread(selectedId!),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['inst-inbox-thread', selectedId] })
      qc.invalidateQueries({ queryKey: ['inst-inbox-threads'] })
      showToast('Thread assigned to you', 'success')
    },
  })

  const closeMut = useMutation({
    mutationFn: () => closeInstInboxThread(selectedId!),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['inst-inbox-thread', selectedId] })
      qc.invalidateQueries({ queryKey: ['inst-inbox-threads'] })
    },
  })

  const bulkMut = useMutation({
    mutationFn: postInstBulkMessage,
    onSuccess: res => {
      showToast(`Message sent to ${res.sent_count} applicants`, 'success')
      setBulkOpen(false)
      qc.invalidateQueries({ queryKey: ['inst-inbox-threads'] })
    },
    onError: () => showToast('Bulk send failed', 'error'),
  })

  return (
    <div className="flex h-[calc(100vh-12rem)] min-h-[480px] flex-col">
      <div className="mb-2 flex items-center justify-end gap-2 px-1">
        <Button size="sm" variant="outline" onClick={() => setBulkOpen(true)}>
          <Users size={14} className="mr-1" />
          Bulk message
        </Button>
      </div>
      <div className="flex flex-1 overflow-hidden rounded-lg border border-border bg-card">
        <InstInboxList
          threads={threads}
          loading={threadsLoading}
          selectedId={selectedId}
          onSelect={setSelectedId}
          filters={filters}
          onFilters={setFilters}
          programOptions={programOptions}
          unassignedCount={unassignedCount}
        />
        {!selectedId ? (
          <div className="flex flex-1 items-center justify-center">
            <EmptyState
              title="Select a thread"
              description="Messages from applicants and prospects land here."
            />
          </div>
        ) : threadLoading || !thread ? (
          <div className="flex flex-1 flex-col p-6 space-y-3">
            <Skeleton className="h-4 w-48" />
            <Skeleton className="h-24 w-full" />
          </div>
        ) : (
          <>
            <InstThreadView
              thread={thread}
              sending={sendMut.isPending}
              onSend={(body, reason, dueDate, aiUsed) =>
                sendMut.mutate({ body, reason, dueDate, aiUsed })
              }
              onAssignToMe={() => assignMut.mutate()}
              assigning={assignMut.isPending}
              onClose={() => closeMut.mutate()}
              closing={closeMut.isPending}
              suggestion={suggestion ?? null}
              suggestionLoading={suggestionLoading}
              onRequestAiDraft={() => refetchSuggestion()}
              onInsertTemplate={() => navigate('/i/communications?tab=templates')}
            />
            <ApplicantContextPanel
              thread={thread}
              onOpenApplicant={appId => navigate(`/i/applications/${appId}`)}
              onOpenChecklist={appId => navigate(`/i/applications/${appId}?tab=checklist`)}
            />
          </>
        )}
      </div>
      <BulkMessageModal
        open={bulkOpen}
        onClose={() => setBulkOpen(false)}
        onSend={payload => bulkMut.mutate(payload)}
        sending={bulkMut.isPending}
      />
    </div>
  )
}
