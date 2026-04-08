import { useState, useEffect, useRef } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Send, Plus, Search, MessageSquare } from 'lucide-react'
import { getConversations, getMessages, sendMessage, createConversation } from '../../api/messaging'
import { getInstitutionPrograms } from '../../api/institutions'
import Badge from '../../components/ui/Badge'
import Button from '../../components/ui/Button'
import Input from '../../components/ui/Input'
import Modal from '../../components/ui/Modal'
import Select from '../../components/ui/Select'
import EmptyState from '../../components/ui/EmptyState'
import Skeleton from '../../components/ui/Skeleton'
import { showToast } from '../../stores/toast-store'
import { formatRelative } from '../../utils/format'
import { STATUS_COLORS } from '../../utils/constants'
import type { Conversation, Message, Program } from '../../types'

export default function MessagingPage() {
  const queryClient = useQueryClient()
  const [selectedConv, setSelectedConv] = useState<string | null>(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [messageText, setMessageText] = useState('')
  const [showNewModal, setShowNewModal] = useState(false)
  const [newStudentId, setNewStudentId] = useState('')
  const [newSubject, setNewSubject] = useState('')
  const [newProgramId, setNewProgramId] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const convsQ = useQuery({ queryKey: ['conversations'], queryFn: getConversations })
  const conversations: Conversation[] = Array.isArray(convsQ.data) ? convsQ.data : []

  const programsQ = useQuery({ queryKey: ['institution-programs'], queryFn: getInstitutionPrograms })
  const programs: Program[] = Array.isArray(programsQ.data) ? programsQ.data : []

  const messagesQ = useQuery({
    queryKey: ['messages', selectedConv],
    queryFn: () => getMessages(selectedConv!),
    enabled: !!selectedConv,
    refetchInterval: 10000,
  })
  const messages: Message[] = Array.isArray(messagesQ.data) ? messagesQ.data : []

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages.length])

  const sendMut = useMutation({
    mutationFn: () => sendMessage(selectedConv!, messageText),
    onSuccess: () => {
      setMessageText('')
      queryClient.invalidateQueries({ queryKey: ['messages', selectedConv] })
      queryClient.invalidateQueries({ queryKey: ['conversations'] })
    },
    onError: () => showToast('Failed to send message', 'error'),
  })

  const createConvMut = useMutation({
    mutationFn: () => createConversation({
      institution_id: '', // filled by backend from auth
      student_id: newStudentId,
      subject: newSubject || undefined,
      program_id: newProgramId || undefined,
    }),
    onSuccess: (data: any) => {
      queryClient.invalidateQueries({ queryKey: ['conversations'] })
      setSelectedConv(data.id)
      setShowNewModal(false)
      setNewStudentId('')
      setNewSubject('')
      setNewProgramId('')
      showToast('Conversation created', 'success')
    },
    onError: () => showToast('Failed to create conversation', 'error'),
  })

  const filteredConvs = conversations.filter(
    c => !searchTerm || (c.subject ?? '').toLowerCase().includes(searchTerm.toLowerCase())
  )

  const selectedConvObj = conversations.find(c => c.id === selectedConv)
  const programOptions = programs.map(p => ({ value: p.id, label: p.program_name }))

  const handleSend = () => {
    if (!messageText.trim()) return
    sendMut.mutate()
  }

  return (
    <div className="flex h-[calc(100vh-64px)]">
      {/* Left: Conversation list */}
      <div className="w-80 border-r border-gray-200 flex flex-col bg-white">
        <div className="p-3 border-b border-gray-200">
          <div className="flex items-center justify-between mb-2">
            <h2 className="text-lg font-semibold text-gray-900">Messages</h2>
            <button onClick={() => setShowNewModal(true)} className="p-1.5 rounded hover:bg-gray-100">
              <Plus size={18} className="text-gray-600" />
            </button>
          </div>
          <div className="relative">
            <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
            <Input
              placeholder="Search conversations..."
              value={searchTerm}
              onChange={e => setSearchTerm(e.target.value)}
              className="pl-9"
            />
          </div>
        </div>

        <div className="flex-1 overflow-y-auto">
          {convsQ.isLoading ? (
            <div className="p-3 space-y-2">{Array.from({ length: 5 }).map((_, i) => <Skeleton key={i} className="h-16" />)}</div>
          ) : filteredConvs.length === 0 ? (
            <p className="text-sm text-gray-500 text-center py-8">No conversations</p>
          ) : (
            filteredConvs.map(conv => (
              <div
                key={conv.id}
                onClick={() => setSelectedConv(conv.id)}
                className={`p-3 border-b border-gray-100 cursor-pointer hover:bg-gray-50 ${selectedConv === conv.id ? 'bg-brand-slate-50' : ''}`}
              >
                <div className="flex items-center justify-between">
                  <p className="text-sm font-medium text-gray-900 truncate">{conv.subject ?? 'No subject'}</p>
                  {(conv.unread_count ?? 0) > 0 && (
                    <span className="ml-2 w-5 h-5 bg-brand-slate-600 text-white text-xs rounded-full flex items-center justify-center">
                      {conv.unread_count}
                    </span>
                  )}
                </div>
                <div className="flex items-center justify-between mt-1">
                  <Badge variant={(STATUS_COLORS[conv.status] as any) ?? 'neutral'} size="sm">{conv.status}</Badge>
                  <span className="text-xs text-gray-400">{formatRelative(conv.last_message_at)}</span>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Right: Message thread */}
      <div className="flex-1 flex flex-col bg-gray-50">
        {!selectedConv ? (
          <div className="flex-1 flex items-center justify-center">
            <EmptyState
              icon={<MessageSquare size={40} />}
              title="Select a conversation"
              description="Choose a conversation from the left or start a new one."
            />
          </div>
        ) : (
          <>
            {/* Header */}
            <div className="px-6 py-3 bg-white border-b border-gray-200">
              <h3 className="text-sm font-semibold text-gray-900">{selectedConvObj?.subject ?? 'Conversation'}</h3>
              <p className="text-xs text-gray-500">Student: {selectedConvObj?.student_id.slice(0, 10)}...</p>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-6 space-y-3">
              {messagesQ.isLoading ? (
                <div className="space-y-3">{Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-12" />)}</div>
              ) : messages.length === 0 ? (
                <p className="text-sm text-gray-500 text-center py-4">No messages yet. Start the conversation!</p>
              ) : (
                messages.map(msg => (
                  <div key={msg.id} className={`flex ${msg.sender_type === 'institution' ? 'justify-end' : 'justify-start'}`}>
                    <div className={`max-w-[70%] rounded-lg px-4 py-2 ${
                      msg.sender_type === 'institution'
                        ? 'bg-brand-slate-600 text-white'
                        : 'bg-white border border-gray-200 text-gray-800'
                    }`}>
                      <p className="text-sm">{msg.message_body}</p>
                      <p className={`text-xs mt-1 ${msg.sender_type === 'institution' ? 'text-brand-slate-200' : 'text-gray-400'}`}>
                        {formatRelative(msg.sent_at)}
                      </p>
                    </div>
                  </div>
                ))
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Input */}
            <div className="p-4 bg-white border-t border-gray-200">
              <div className="flex gap-2">
                <Input
                  className="flex-1"
                  placeholder="Type a message..."
                  value={messageText}
                  onChange={e => setMessageText(e.target.value)}
                  onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend() } }}
                />
                <Button onClick={handleSend} disabled={!messageText.trim() || sendMut.isPending} className="flex items-center gap-2">
                  <Send size={16} /> Send
                </Button>
              </div>
            </div>
          </>
        )}
      </div>

      {/* New Conversation Modal */}
      <Modal isOpen={showNewModal} onClose={() => setShowNewModal(false)} title="New Conversation">
        <div className="space-y-4">
          <Input label="Student ID *" value={newStudentId} onChange={e => setNewStudentId(e.target.value)} placeholder="Paste student ID" />
          <Input label="Subject" value={newSubject} onChange={e => setNewSubject(e.target.value)} placeholder="Conversation subject" />
          <Select label="Program" options={programOptions} placeholder="Select program (optional)" value={newProgramId} onChange={e => setNewProgramId(e.target.value)} />
          <div className="flex justify-end gap-2">
            <Button variant="ghost" onClick={() => setShowNewModal(false)}>Cancel</Button>
            <Button onClick={() => createConvMut.mutate()} disabled={!newStudentId || createConvMut.isPending}>
              {createConvMut.isPending ? 'Creating...' : 'Create'}
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  )
}
