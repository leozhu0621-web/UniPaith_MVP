import { useState, useEffect, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getConversations, getMessages, sendMessage } from '../../api/messaging'
import { listDocuments } from '../../api/documents'
import Badge from '../../components/ui/Badge'
import Button from '../../components/ui/Button'
import Skeleton from '../../components/ui/Skeleton'
import { formatRelative } from '../../utils/format'
import {
  Send, Paperclip, Building2, FileText, AlertCircle, CheckCircle2,
  Clock, MessageSquare, Bell, ExternalLink,
} from 'lucide-react'
import type { Conversation, Message } from '../../types'

type MsgFilter = 'all' | 'human' | 'system'
type ActionState = 'needs_reply' | 'doc_requested' | 'clarification' | 'overdue' | 'completed' | null

const ACTION_CONFIG: Record<string, { label: string; variant: 'danger' | 'warning' | 'info' | 'success' | 'neutral'; icon: typeof AlertCircle }> = {
  needs_reply: { label: 'Needs Reply', variant: 'danger', icon: AlertCircle },
  doc_requested: { label: 'Doc Requested', variant: 'warning', icon: FileText },
  clarification: { label: 'Clarification', variant: 'info', icon: MessageSquare },
  overdue: { label: 'Overdue', variant: 'danger', icon: Clock },
  completed: { label: 'Completed', variant: 'success', icon: CheckCircle2 },
}

function deriveActionState(conv: Conversation): ActionState {
  if (conv.status === 'resolved' || conv.status === 'closed') return 'completed'
  if (conv.status === 'awaiting_response') return 'needs_reply'
  if (conv.unread_count && conv.unread_count > 0) return 'needs_reply'
  return null
}

function isSystemThread(conv: Conversation): boolean {
  const subject = (conv.subject || '').toLowerCase()
  return subject.includes('alert') || subject.includes('confirmation') ||
    subject.includes('notification') || subject.includes('system') ||
    subject.includes('reminder') || subject.includes('update')
}

export default function MessagesPage() {
  const { convId } = useParams<{ convId: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [selectedConv, setSelectedConv] = useState<string | null>(convId || null)
  const [newMessage, setNewMessage] = useState('')
  const [msgFilter, setMsgFilter] = useState<MsgFilter>('all')
  const [showAttachments, setShowAttachments] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const { data: conversations, isLoading: convsLoading } = useQuery({
    queryKey: ['conversations'],
    queryFn: getConversations,
    refetchInterval: 30000,
  })

  const { data: messages } = useQuery({
    queryKey: ['messages', selectedConv],
    queryFn: () => getMessages(selectedConv!, { limit: 50 }),
    enabled: !!selectedConv,
    refetchInterval: 5000,
  })

  const { data: documents } = useQuery({
    queryKey: ['my-documents'],
    queryFn: listDocuments,
    enabled: showAttachments,
  })

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  useEffect(() => {
    if (convId && convId !== selectedConv) setSelectedConv(convId)
  }, [convId, selectedConv])

  const sendMut = useMutation({
    mutationFn: (content: string) => sendMessage(selectedConv!, content),
    onSuccess: () => {
      setNewMessage('')
      queryClient.invalidateQueries({ queryKey: ['messages', selectedConv] })
      queryClient.invalidateQueries({ queryKey: ['conversations'] })
    },
  })

  const handleSend = () => {
    const trimmed = newMessage.trim()
    if (!trimmed || sendMut.isPending) return
    sendMut.mutate(trimmed)
  }

  const handleAttach = (docName: string) => {
    setNewMessage(prev => `${prev}\n[Attached: ${docName}]`)
    setShowAttachments(false)
  }

  const convList: Conversation[] = Array.isArray(conversations) ? conversations : []
  const msgList: Message[] = Array.isArray(messages) ? messages : []
  const docList: any[] = Array.isArray(documents) ? documents : []

  const filteredConvs = convList.filter(c => {
    if (msgFilter === 'human') return !isSystemThread(c)
    if (msgFilter === 'system') return isSystemThread(c)
    return true
  })

  const selectedConvObj = convList.find(c => c.id === selectedConv)

  return (
    <div className="flex h-full">
      {/* Left: conversation list */}
      <div className="w-80 border-r border-gray-200 bg-white flex flex-col">
        <div className="p-3 border-b border-gray-100">
          <h2 className="font-semibold text-sm mb-2">Messages</h2>
          <div className="flex gap-1">
            {([['all', 'All'], ['human', 'Human'], ['system', 'System']] as [MsgFilter, string][]).map(([key, label]) => (
              <button
                key={key}
                onClick={() => setMsgFilter(key)}
                className={`px-2.5 py-1 text-xs rounded-full transition-colors ${msgFilter === key ? 'bg-stone-700 text-white' : 'bg-gray-100 text-gray-500 hover:bg-gray-200'}`}
              >
                {key === 'system' && <Bell size={10} className="inline mr-1" />}
                {key === 'human' && <MessageSquare size={10} className="inline mr-1" />}
                {label}
              </button>
            ))}
          </div>
        </div>
        <div className="flex-1 overflow-y-auto">
          {convsLoading ? (
            <div className="p-3 space-y-3">{Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-14" />)}</div>
          ) : filteredConvs.length === 0 ? (
            <p className="p-4 text-sm text-gray-500">No conversations</p>
          ) : (
            filteredConvs.map(c => {
              const action = deriveActionState(c)
              const isSys = isSystemThread(c)
              return (
                <button
                  key={c.id}
                  onClick={() => { setSelectedConv(c.id); navigate(`/s/messages/${c.id}`) }}
                  className={`w-full text-left px-3 py-3 border-b border-gray-50 hover:bg-gray-50 ${selectedConv === c.id ? 'bg-gray-100' : ''} ${isSys ? 'bg-gray-50/50' : ''}`}
                >
                  <div className="flex items-center justify-between">
                    <p className="text-sm font-medium truncate flex-1">{c.subject || 'Conversation'}</p>
                    {c.unread_count ? (
                      <span className="ml-2 w-5 h-5 bg-red-500 text-white text-[10px] rounded-full flex items-center justify-center flex-shrink-0">
                        {c.unread_count}
                      </span>
                    ) : null}
                  </div>
                  <div className="flex items-center gap-2 mt-1">
                    {c.program_id && (
                      <span className="inline-flex items-center gap-0.5 text-[10px] text-purple-600">
                        <Building2 size={9} /> Program
                      </span>
                    )}
                    {isSys && <Badge variant="neutral" size="sm">System</Badge>}
                    {action && (
                      <Badge variant={ACTION_CONFIG[action].variant} size="sm">
                        {ACTION_CONFIG[action].label}
                      </Badge>
                    )}
                  </div>
                  <p className="text-[10px] text-gray-400 mt-0.5">{formatRelative(c.last_message_at)}</p>
                </button>
              )
            })
          )}
        </div>
      </div>

      {/* Right: messages */}
      <div className="flex-1 flex flex-col">
        {!selectedConv ? (
          <div className="flex-1 flex items-center justify-center text-gray-400 text-sm">
            Select a conversation
          </div>
        ) : (
          <>
            {/* Thread header */}
            {selectedConvObj && (
              <div className="px-4 py-2.5 border-b border-gray-200 bg-white flex items-center justify-between">
                <div className="min-w-0">
                  <p className="text-sm font-medium truncate">{selectedConvObj.subject || 'Conversation'}</p>
                  <div className="flex items-center gap-2 mt-0.5">
                    {selectedConvObj.program_id && (
                      <button
                        onClick={() => navigate(`/s/programs/${selectedConvObj.program_id}`)}
                        className="inline-flex items-center gap-1 text-[10px] text-purple-600 hover:underline"
                      >
                        <Building2 size={10} /> View Program <ExternalLink size={8} />
                      </button>
                    )}
                    {(selectedConvObj as any).application_id && (
                      <button
                        onClick={() => navigate(`/s/applications/${(selectedConvObj as any).application_id}`)}
                        className="inline-flex items-center gap-1 text-[10px] text-student hover:underline"
                      >
                        <ExternalLink size={8} /> View Application
                      </button>
                    )}
                    {deriveActionState(selectedConvObj) && (
                      <Badge variant={ACTION_CONFIG[deriveActionState(selectedConvObj)!].variant} size="sm">
                        {ACTION_CONFIG[deriveActionState(selectedConvObj)!].label}
                      </Badge>
                    )}
                  </div>
                </div>
                {deriveActionState(selectedConvObj) === 'needs_reply' && (
                  <Button size="sm" variant="secondary" onClick={() => {}}>
                    <CheckCircle2 size={12} className="mr-1" /> Mark Complete
                  </Button>
                )}
              </div>
            )}

            {/* Messages */}
            <div className="flex-1 overflow-y-auto px-6 py-4 space-y-3">
              {msgList.map(msg => {
                const isOwn = msg.sender_type === 'student'
                const isSysMsg = msg.sender_type === 'institution' && (msg.message_body || '').startsWith('[')
                return (
                  <div key={msg.id} className={`flex ${isOwn ? 'justify-end' : 'justify-start'}`}>
                    <div className={`max-w-[70%] px-4 py-2 rounded-2xl text-sm ${
                      isOwn
                        ? 'bg-stone-700 text-white rounded-br-md'
                        : isSysMsg
                          ? 'bg-gray-50 text-gray-500 rounded-bl-md border border-gray-200'
                          : 'bg-gray-100 text-stone-700 rounded-bl-md'
                    }`}>
                      {msg.message_body}
                      <p className={`text-[10px] mt-1 ${isOwn ? 'text-white/60' : 'text-gray-400'}`}>
                        {formatRelative(msg.sent_at)}
                      </p>
                    </div>
                  </div>
                )
              })}
              <div ref={messagesEndRef} />
            </div>

            {/* Input */}
            <div className="px-4 py-3 border-t border-gray-200 bg-white">
              {showAttachments && (
                <div className="mb-2 p-2 bg-gray-50 rounded-lg border max-h-32 overflow-y-auto">
                  <p className="text-xs text-gray-500 mb-1">Attach from your materials:</p>
                  {docList.length > 0 ? docList.slice(0, 10).map((doc: any) => (
                    <button
                      key={doc.id}
                      onClick={() => handleAttach(doc.file_name || doc.name || 'Document')}
                      className="block w-full text-left text-xs text-stone-700 hover:bg-gray-100 px-2 py-1 rounded"
                    >
                      <FileText size={10} className="inline mr-1" />
                      {doc.file_name || doc.name || 'Document'}
                    </button>
                  )) : (
                    <p className="text-xs text-gray-400">No documents uploaded yet</p>
                  )}
                </div>
              )}
              <div className="flex gap-2">
                <button
                  onClick={() => setShowAttachments(!showAttachments)}
                  className={`p-2 rounded-lg transition-colors ${showAttachments ? 'bg-stone-100 text-stone-700' : 'text-gray-400 hover:text-stone-600'}`}
                >
                  <Paperclip size={16} />
                </button>
                <input
                  value={newMessage}
                  onChange={e => setNewMessage(e.target.value)}
                  onKeyDown={e => e.key === 'Enter' && !e.shiftKey && (e.preventDefault(), handleSend())}
                  placeholder="Type a message..."
                  className="flex-1 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-stone-700"
                />
                <button onClick={handleSend} disabled={!newMessage.trim()} className="p-2 bg-stone-700 text-white rounded-lg hover:bg-stone-600 disabled:opacity-50">
                  <Send size={16} />
                </button>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
