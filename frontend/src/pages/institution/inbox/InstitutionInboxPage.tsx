import { useCallback, useEffect, useMemo, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Users } from 'lucide-react'
import Button from '../../../components/ui/Button'
import Skeleton from '../../../components/ui/Skeleton'
import { getInstitutionPrograms, getSegments, getTemplates } from '../../../api/institutions'
import {
  assignThread,
  closeThread,
  getInstAiDraft,
  getInstThread,
  getInstThreads,
  getStaffRoster,
  postInstMessage,
} from '../../../api/institution-inbox'
import type { InstSuggestedReply, InstThreadSummary } from '../../../types'
import InboxThreadList, { type InstInboxFilters } from './InboxThreadList'
import InboxThreadView from './InboxThreadView'
import ApplicantContextPanel from './ApplicantContextPanel'
import BulkMessageSheet from './BulkMessageSheet'
import type { SendPayload } from './ReplyComposer'

const DEFAULT_FILTERS: InstInboxFilters = {
  filter: 'all',
  reason: 'all',
  program_id: 'all',
  state: 'all',
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

export default function InstitutionInboxPage() {
  const navigate = useNavigate()
  const qc = useQueryClient()
  const [searchParams, setSearchParams] = useSearchParams()
  const selectedId = searchParams.get('thread')
  const [filters, setFilters] = useState<InstInboxFilters>(DEFAULT_FILTERS)
  const [bulkOpen, setBulkOpen] = useState(false)

  // AI draft is on-demand per thread (spec 29 §8).
  const [aiDraft, setAiDraft] = useState<InstSuggestedReply | null>(null)
  const [aiDraftLoading, setAiDraftLoading] = useState(false)
  const [aiDraftRequested, setAiDraftRequested] = useState(false)

  const apiFilters = useMemo(
    () => ({
      filter: filters.filter,
      ...(filters.reason !== 'all' ? { reason: filters.reason } : {}),
      ...(filters.program_id !== 'all' ? { program_id: filters.program_id } : {}),
      ...(filters.state !== 'all' ? { state: filters.state } : {}),
    }),
    [filters],
  )

  const { data: threadsData, isLoading: threadsLoading } = useQuery({
    queryKey: ['inst-inbox-threads', apiFilters],
    queryFn: () => getInstThreads(apiFilters),
    refetchInterval: 20000,
  })
  const threads: InstThreadSummary[] = useMemo(
    () => (Array.isArray(threadsData) ? threadsData : []),
    [threadsData],
  )

  const { data: thread, isLoading: threadLoading } = useQuery({
    queryKey: ['inst-inbox-thread', selectedId],
    queryFn: () => getInstThread(selectedId!),
    enabled: !!selectedId,
    refetchInterval: 20000,
  })

  const { data: rosterData } = useQuery({ queryKey: ['inst-inbox-staff'], queryFn: getStaffRoster })
  const roster = Array.isArray(rosterData) ? rosterData : []

  const { data: programsData } = useQuery({
    queryKey: ['institution-programs'],
    queryFn: getInstitutionPrograms,
  })
  const { data: templatesData } = useQuery({
    queryKey: ['communication-templates'],
    queryFn: () => getTemplates(),
  })
  const templates = Array.isArray(templatesData) ? templatesData : []
  const { data: segmentsData } = useQuery({ queryKey: ['institution-segments'], queryFn: getSegments })
  const segments = Array.isArray(segmentsData) ? segmentsData : []

  const programOptions = useMemo(() => {
    const list = Array.isArray(programsData) ? programsData : []
    return [
      { value: 'all', label: 'All programs' },
      ...list.map((p: { id: string; program_name: string }) => ({
        value: p.id,
        label: p.program_name,
      })),
    ]
  }, [programsData])

  // Reset the AI draft when switching threads.
  useEffect(() => {
    setAiDraft(null)
    setAiDraftLoading(false)
    setAiDraftRequested(false)
  }, [selectedId])

  const openThread = (id: string) => {
    setSearchParams({ tab: 'inbox', thread: id }, { replace: true })
  }
  const closeThreadView = () => {
    setSearchParams({ tab: 'inbox' }, { replace: true })
  }

  const sendMut = useMutation({
    mutationFn: (payload: SendPayload) => postInstMessage(selectedId!, payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['inst-inbox-thread', selectedId] })
      qc.invalidateQueries({ queryKey: ['inst-inbox-threads'] })
    },
  })

  const assignMut = useMutation({
    mutationFn: (staffUserId: string | null) => assignThread(selectedId!, staffUserId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['inst-inbox-thread', selectedId] })
      qc.invalidateQueries({ queryKey: ['inst-inbox-threads'] })
    },
  })

  const closeMut = useMutation({
    mutationFn: () => closeThread(selectedId!),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['inst-inbox-thread', selectedId] })
      qc.invalidateQueries({ queryKey: ['inst-inbox-threads'] })
    },
  })

  const requestAiDraft = useCallback(async () => {
    if (!selectedId) return
    setAiDraftLoading(true)
    setAiDraftRequested(true)
    try {
      const res = await getInstAiDraft(selectedId)
      setAiDraft(res)
    } catch {
      setAiDraft(null)
    } finally {
      setAiDraftLoading(false)
    }
  }, [selectedId])

  return (
    <div className="flex h-full">
      {/* Left: thread list */}
      <div
        className={`${selectedId ? 'hidden xl:flex' : 'flex'} w-full flex-col border-r border-border bg-card xl:w-80`}
      >
        <div className="flex items-center justify-between gap-2 border-b border-border px-3 py-2">
          <span className="text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
            Communications
          </span>
          <Button variant="secondary" size="sm" onClick={() => setBulkOpen(true)}>
            <Users size={13} className="mr-1.5" /> Message segment
          </Button>
        </div>
        <div className="min-h-0 flex-1">
          <InboxThreadList
            threads={threads}
            loading={threadsLoading}
            selectedId={selectedId}
            onSelect={openThread}
            filters={filters}
            onFilters={setFilters}
            programOptions={programOptions}
          />
        </div>
      </div>

      {/* Center: conversation */}
      <div className={`${selectedId ? 'flex' : 'hidden xl:flex'} min-w-0 flex-1 flex-col`}>
        {!selectedId ? (
          <div className="flex flex-1 items-center justify-center px-6 text-center text-sm text-muted-foreground">
            Pick a conversation to see it here.
          </div>
        ) : threadLoading || !thread ? (
          <ThreadSkeleton />
        ) : (
          <InboxThreadView
            thread={thread}
            roster={roster}
            onBack={closeThreadView}
            onAssign={staffUserId => assignMut.mutate(staffUserId)}
            onClose={() => closeMut.mutate()}
            closing={closeMut.isPending}
            onSend={payload => sendMut.mutate(payload)}
            sending={sendMut.isPending}
            templates={templates}
            aiDraft={aiDraft}
            aiDraftLoading={aiDraftLoading}
            aiDraftRequested={aiDraftRequested}
            onRequestAiDraft={requestAiDraft}
          />
        )}
      </div>

      {/* Right: applicant context rail (operational desktop) */}
      {selectedId && thread && (
        <div className="hidden w-72 shrink-0 overflow-y-auto border-l border-border bg-background p-3 xl:block">
          <ApplicantContextPanel thread={thread} onNavigate={navigate} />
        </div>
      )}

      <BulkMessageSheet
        isOpen={bulkOpen}
        onClose={() => setBulkOpen(false)}
        segments={segments}
        templates={templates}
      />
    </div>
  )
}
