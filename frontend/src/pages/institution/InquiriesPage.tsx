import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Inbox, MessageSquare, CheckCircle2, Clock, User } from 'lucide-react'
import { getInquiries, updateInquiry } from '../../api/institutions'
import Card from '../../components/ui/Card'
import Badge from '../../components/ui/Badge'
import Button from '../../components/ui/Button'
import Modal from '../../components/ui/Modal'
import Textarea from '../../components/ui/Textarea'
import Tabs from '../../components/ui/Tabs'
import EmptyState from '../../components/ui/EmptyState'
import Skeleton from '../../components/ui/Skeleton'
import InstitutionPageHeader from '../../components/institution/InstitutionPageHeader'
import { showToast } from '../../stores/toast-store'
import { formatDateTime } from '../../utils/format'
import type { Inquiry } from '../../types'

const STATUS_BADGE: Record<string, 'neutral' | 'info' | 'success' | 'warning'> = {
  new: 'warning',
  in_progress: 'info',
  responded: 'success',
  closed: 'neutral',
}

export default function InquiriesPage() {
  const queryClient = useQueryClient()
  const [activeTab, setActiveTab] = useState('all')
  const [selected, setSelected] = useState<Inquiry | null>(null)
  const [responseText, setResponseText] = useState('')

  const tabs = [
    { id: 'all', label: 'All' },
    { id: 'new', label: 'New' },
    { id: 'in_progress', label: 'In Progress' },
    { id: 'responded', label: 'Responded' },
    { id: 'closed', label: 'Closed' },
  ]

  const statusFilter = activeTab === 'all' ? undefined : activeTab
  const inquiriesQ = useQuery({
    queryKey: ['inquiries', statusFilter],
    queryFn: () => getInquiries(statusFilter),
  })
  const inquiries: Inquiry[] = Array.isArray(inquiriesQ.data) ? inquiriesQ.data : []

  const respondMut = useMutation({
    mutationFn: (p: { id: string; response_text: string }) =>
      updateInquiry(p.id, { response_text: p.response_text, status: 'responded' }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['inquiries'] })
      showToast('Response sent', 'success')
      setSelected(null)
      setResponseText('')
    },
  })

  const statusMut = useMutation({
    mutationFn: (p: { id: string; status: string }) =>
      updateInquiry(p.id, { status: p.status }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['inquiries'] })
      showToast('Status updated', 'success')
    },
  })

  const openDetail = (inq: Inquiry) => {
    setSelected(inq)
    setResponseText(inq.response_text || '')
  }

  const newCount = inquiries.filter(i => i.status === 'new').length

  return (
    <div className="p-6 space-y-4">
      <InstitutionPageHeader
        title="Inquiry Queue"
        description="Manage information requests from prospective students."
      />

      {inquiries.length > 0 && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          <Card className="p-3">
            <p className="text-xs text-gray-500">Total</p>
            <p className="text-xl font-semibold text-gray-900">{inquiries.length}</p>
          </Card>
          <Card className="p-3 border-amber-200">
            <p className="text-xs text-amber-600">New</p>
            <p className="text-xl font-bold text-amber-600">{newCount}</p>
          </Card>
          <Card className="p-3">
            <p className="text-xs text-gray-500">In Progress</p>
            <p className="text-xl font-semibold text-gray-900">{inquiries.filter(i => i.status === 'in_progress').length}</p>
          </Card>
          <Card className="p-3">
            <p className="text-xs text-gray-500">Responded</p>
            <p className="text-xl font-semibold text-gray-900">{inquiries.filter(i => i.status === 'responded').length}</p>
          </Card>
        </div>
      )}

      <Tabs tabs={tabs} activeTab={activeTab} onChange={setActiveTab} />

      {inquiriesQ.isLoading ? (
        <div className="space-y-3">{Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-24" />)}</div>
      ) : inquiries.length === 0 ? (
        <EmptyState
          icon={<Inbox size={40} />}
          title="No inquiries"
          description="When students request info from your school or program pages, their inquiries will appear here."
        />
      ) : (
        <div className="space-y-2">
          {inquiries.map(inq => (
            <Card key={inq.id} className="p-4 cursor-pointer hover:shadow-md transition-shadow" onClick={() => openDetail(inq)}>
              <div className="flex items-start justify-between mb-1">
                <div className="flex items-center gap-2">
                  <h3 className="font-semibold text-gray-900 text-sm">{inq.subject}</h3>
                  <Badge variant={STATUS_BADGE[inq.status] ?? 'neutral'}>{inq.status.replace('_', ' ')}</Badge>
                </div>
                {inq.program_name && <Badge variant="info">{inq.program_name}</Badge>}
              </div>
              <div className="flex items-center gap-3 text-xs text-gray-500 mt-1">
                <span className="flex items-center gap-1"><User size={12} /> {inq.student_name}</span>
                <span>{inq.student_email}</span>
                <span className="flex items-center gap-1"><Clock size={12} /> {formatDateTime(inq.created_at)}</span>
              </div>
              <p className="text-sm text-gray-600 mt-2 line-clamp-2">{inq.message}</p>
            </Card>
          ))}
        </div>
      )}

      {/* Detail / Respond Modal */}
      <Modal isOpen={!!selected} onClose={() => setSelected(null)} title={selected?.subject ?? ''}>
        {selected && (
          <div className="space-y-4">
            <div className="flex items-center gap-3 text-sm text-gray-600">
              <span className="flex items-center gap-1"><User size={14} /> {selected.student_name}</span>
              <span>{selected.student_email}</span>
              <Badge variant={STATUS_BADGE[selected.status]}>{selected.status.replace('_', ' ')}</Badge>
            </div>
            {selected.program_name && (
              <Badge variant="info">Program: {selected.program_name}</Badge>
            )}
            <Card className="p-3 bg-gray-50">
              <p className="text-xs text-gray-500 mb-1">Student's message</p>
              <p className="text-sm text-gray-800 whitespace-pre-wrap">{selected.message}</p>
            </Card>
            <p className="text-xs text-gray-400">Received: {formatDateTime(selected.created_at)}</p>

            {selected.response_text && selected.responded_at && (
              <Card className="p-3 bg-green-50 border-green-200">
                <p className="text-xs text-green-600 mb-1 flex items-center gap-1"><CheckCircle2 size={12} /> Responded {formatDateTime(selected.responded_at)}</p>
                <p className="text-sm text-gray-800 whitespace-pre-wrap">{selected.response_text}</p>
              </Card>
            )}

            <Textarea
              label="Your Response"
              value={responseText}
              onChange={e => setResponseText(e.target.value)}
              rows={4}
              placeholder="Type your response to the student..."
            />

            <div className="flex items-center justify-between">
              <div className="flex gap-2">
                {selected.status === 'new' && (
                  <Button variant="ghost" size="sm" onClick={() => statusMut.mutate({ id: selected.id, status: 'in_progress' })}>
                    Mark In Progress
                  </Button>
                )}
                {selected.status !== 'closed' && (
                  <Button variant="ghost" size="sm" onClick={() => statusMut.mutate({ id: selected.id, status: 'closed' })}>
                    Close
                  </Button>
                )}
              </div>
              <Button
                onClick={() => respondMut.mutate({ id: selected.id, response_text: responseText })}
                disabled={respondMut.isPending || !responseText.trim()}
                className="flex items-center gap-2"
              >
                <MessageSquare size={14} /> {respondMut.isPending ? 'Sending...' : 'Send Response'}
              </Button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  )
}
