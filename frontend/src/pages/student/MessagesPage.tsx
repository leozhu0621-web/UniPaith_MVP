import { useState, useEffect, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getConversations, getMessages, sendMessage } from '../../api/messaging'
import Skeleton from '../../components/ui/Skeleton'
import { formatRelative } from '../../utils/format'
import { Send } from 'lucide-react'
import type { Conversation, Message } from '../../types'

export default function MessagesPage() {
  const { convId } = useParams<{ convId: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [selectedConv, setSelectedConv] = useState<string | null>(convId || null)
  const [newMessage, setNewMessage] = useState('')
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

  const convList: Conversation[] = conversations ?? []
  const msgList: Message[] = messages ?? []

  return (
    <div className="flex h-full">
      {/* Left: conversation list */}
      <div className="w-72 border-r border-gray-200 bg-white flex flex-col">
        <div className="p-3 border-b border-gray-100">
          <h2 className="font-semibold text-sm">Messages</h2>
        </div>
        <div className="flex-1 overflow-y-auto">
          {convsLoading ? (
            <div className="p-3 space-y-3">{Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-14" />)}</div>
          ) : convList.length === 0 ? (
            <p className="p-4 text-sm text-gray-500">No conversations yet</p>
          ) : (
            convList.map(c => (
              <button
                key={c.id}
                onClick={() => { setSelectedConv(c.id); navigate(`/s/messages/${c.id}`) }}
                className={`w-full text-left px-3 py-3 border-b border-gray-50 hover:bg-gray-50 ${selectedConv === c.id ? 'bg-gray-100' : ''}`}
              >
                <p className="text-sm font-medium truncate">{c.subject || 'Conversation'}</p>
                <p className="text-xs text-gray-400 mt-0.5">{formatRelative(c.last_message_at)}</p>
              </button>
            ))
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
            <div className="flex-1 overflow-y-auto px-6 py-4 space-y-3">
              {msgList.map(msg => {
                const isOwn = msg.sender_type === 'student'
                return (
                  <div key={msg.id} className={`flex ${isOwn ? 'justify-end' : 'justify-start'}`}>
                    <div className={`max-w-[70%] px-4 py-2 rounded-2xl text-sm ${isOwn ? 'bg-gray-900 text-white rounded-br-md' : 'bg-gray-100 text-gray-800 rounded-bl-md'}`}>
                      {msg.message_body}
                    </div>
                  </div>
                )
              })}
              <div ref={messagesEndRef} />
            </div>
            <div className="px-4 py-3 border-t border-gray-200 bg-white flex gap-2">
              <input
                value={newMessage}
                onChange={e => setNewMessage(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && !e.shiftKey && (e.preventDefault(), handleSend())}
                placeholder="Type a message..."
                className="flex-1 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-gray-900"
              />
              <button onClick={handleSend} disabled={!newMessage.trim()} className="p-2 bg-gray-900 text-white rounded-lg hover:bg-gray-800 disabled:opacity-50">
                <Send size={16} />
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
