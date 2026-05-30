import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getConversations, getMessages, sendMessage } from '../../api/messaging'
import { listDocuments } from '../../api/documents'
import Badge from '../../components/ui/Badge'
import Button from '../../components/ui/Button'
import Skeleton from '../../components/ui/Skeleton'
import { formatRelative } from '../../utils/format'
import {
  Send, Paperclip, Building2, FileText, AlertCircle, CheckCircle2,
  Clock, MessageSquare, Bell, ExternalLink, ChevronLeft,
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

export default function MessagesPage({ initialThreadId }: { initialThreadId?: string | null }) {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [selectedConv, setSelectedConv] = useState<string | null>(initialThreadId || null)
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
    if (initialThreadId && initialThreadId !== selectedConv) setSelectedConv(initialThreadId)
  }, [initialThreadId, selectedConv])

  const openThread = (id: string) => {
    setSelectedConv(id)
    navigate(`/s/manage?tab=messages&thread=${id}`, { replace: true })
  }

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
      {/* Left: conversation list. Mobile (Spec/02b §5): list and thread are
          separate full screens — show the list only when no thread is open. */}
      <div className={`${selectedConv ? 'hidden lg:flex' : 'flex'} w-full lg:w-80 border-r border-border bg-card flex-col`}>
        <div className="p-3 border-b border-border">
          <h2 className="font-semibold text-sm mb-2">Messages</h2>
          <div className="flex gap-1">
            {([['all', 'All'], ['human', 'Human'], ['system', 'System']] as [MsgFilter, string][]).map(([key, label]) => (
              <button
                key={key}
                onClick={() => setMsgFilter(key)}
                className={`px-2.5 py-1 text-xs rounded-full transition-colors ${msgFilter === key ? 'bg-cobalt text-white' : 'bg-muted text-muted-foreground hover:brightness-95'}`}
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
            <p className="p-4 text-sm text-muted-foreground">No conversations</p>
          ) : (
            filteredConvs.map(c => {
              const action = deriveActionState(c)
              const isSys = isSystemThread(c)
              return (
                <button
                  key={c.id}
                  onClick={() => openThread(c.id)}
                  className={`w-full text-left px-3 py-3 border-b border-divider hover:bg-muted ${selectedConv === c.id ? 'bg-muted' : ''} ${isSys ? 'bg-muted/40' : ''}`}
                >
                  <div className="flex items-center justify-between">
                    <p className="text-sm font-medium truncate flex-1">{c.subject || 'Conversation'}</p>
                    {c.unread_count ? (
                      <span className="ml-2 w-5 h-5 bg-error text-white text-[10px] rounded-full flex items-center justify-center flex-shrink-0">
                        {c.unread_count}
                      </span>
                    ) : null}
                  </div>
                  <div className="flex items-center gap-2 mt-1">
                    {c.program_id && (
                      <span className="inline-flex items-center gap-0.5 text-[10px] text-cobalt">
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
                  <p className="text-[10px] text-muted-foreground mt-0.5">{formatRelative(c.last_message_at)}</p>
                </button>
              )
            })
          )}
        </div>
      </div>

      {/* Right: messages. Mobile: full screen when a thread is selected. */}
      <div className={`${selectedConv ? 'flex' : 'hidden lg:flex'} flex-1 flex-col`}>
        {!selectedConv ? (
          <div className="flex-1 flex items-center justify-center text-muted-foreground text-sm">
            Select a conversation
          </div>
        ) : (
          <>
            {/* Thread header */}
            {selectedConvObj && (
              <div className="px-4 py-2.5 border-b border-border bg-card flex items-center justify-between gap-2">
                <button
                  onClick={() => { setSelectedConv(null); navigate('/s/manage?tab=messages') }}
                  className="lg:hidden p-1 -ml-1 rounded-md text-muted-foreground hover:bg-muted shrink-0"
                  aria-label="Back to messages"
                >
                  <ChevronLeft size={18} />
                </button>
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-medium truncate">{selectedConvObj.subject || 'Conversation'}</p>
                  <div className="flex items-center gap-2 mt-0.5">
                    {selectedConvObj.program_id && (
                      <button
                        onClick={() => navigate(`/s/programs/${selectedConvObj.program_id}`)}
                        className="inline-flex items-center gap-1 text-[10px] text-cobalt hover:underline"
                      >
                        <Building2 size={10} /> View Program <ExternalLink size={8} />
                      </button>
                    )}
                    {(selectedConvObj as any).application_id && (
                      <button
                        onClick={() => navigate(`/s/applications/${(selectedConvObj as any).application_id}`)}
                        className="inline-flex items-center gap-1 text-[10px] text-cobalt hover:underline"
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
                        ? 'bg-cobalt text-white rounded-br-md'
                        : isSysMsg
                          ? 'bg-muted text-muted-foreground rounded-bl-md border border-border'
                          : 'bg-muted text-charcoal rounded-bl-md'
                    }`}>
                      {msg.message_body}
                      <p className={`text-[10px] mt-1 ${isOwn ? 'text-white/60' : 'text-muted-foreground'}`}>
                        {formatRelative(msg.sent_at)}
                      </p>
                    </div>
                  </div>
                )
              })}
              <div ref={messagesEndRef} />
            </div>

            {/* Input */}
            <div className="px-4 py-3 border-t border-border bg-card">
              {showAttachments && (
                <div className="mb-2 p-2 bg-muted rounded-lg border max-h-32 overflow-y-auto">
                  <p className="text-xs text-muted-foreground mb-1">Attach from your materials:</p>
                  {docList.length > 0 ? docList.slice(0, 10).map((doc: any) => (
                    <button
                      key={doc.id}
                      onClick={() => handleAttach(doc.file_name || doc.name || 'Document')}
                      className="block w-full text-left text-xs text-charcoal hover:bg-muted px-2 py-1 rounded"
                    >
                      <FileText size={10} className="inline mr-1" />
                      {doc.file_name || doc.name || 'Document'}
                    </button>
                  )) : (
                    <p className="text-xs text-muted-foreground">No documents uploaded yet</p>
                  )}
                </div>
              )}
              <div className="flex gap-2">
                <button
                  onClick={() => setShowAttachments(!showAttachments)}
                  className={`p-2 rounded-lg transition-colors ${showAttachments ? 'bg-muted text-charcoal' : 'text-muted-foreground hover:text-charcoal'}`}
                >
                  <Paperclip size={16} />
                </button>
                <input
                  value={newMessage}
                  onChange={e => setNewMessage(e.target.value)}
                  onKeyDown={e => e.key === 'Enter' && !e.shiftKey && (e.preventDefault(), handleSend())}
                  placeholder="Type a message..."
                  className="flex-1 border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                />
                <button onClick={handleSend} disabled={!newMessage.trim()} className="p-2 bg-cobalt text-white rounded-lg hover:bg-cobalt-dark disabled:opacity-50">
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
