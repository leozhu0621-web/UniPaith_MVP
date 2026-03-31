import { useState, useEffect, useRef } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getConversations, getMessages, sendMessage, createConversation } from '../../api/messaging'
import { useAuthStore } from '../../stores/auth-store'
import { Paperclip, ArrowUp } from 'lucide-react'
import Avatar from '../../components/ui/Avatar'
import { formatRelative } from '../../utils/format'
import Skeleton from '../../components/ui/Skeleton'
import type { Message } from '../../types'

const QUICK_ACTIONS = ['Update GPA', 'My matches', 'Upload document', 'Help with essay']

export default function ChatPage() {
  const user = useAuthStore(s => s.user)
  const queryClient = useQueryClient()
  const [input, setInput] = useState('')
  const [activeConvId, setActiveConvId] = useState<string | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const { data: conversations } = useQuery({
    queryKey: ['conversations'],
    queryFn: getConversations,
  })

  // Auto-select first conversation (AI advisor)
  useEffect(() => {
    if (conversations?.length && !activeConvId) {
      setActiveConvId(conversations[0].id)
    }
  }, [conversations, activeConvId])

  const { data: messages, isLoading: messagesLoading } = useQuery({
    queryKey: ['messages', activeConvId],
    queryFn: () => getMessages(activeConvId!, { limit: 50 }),
    enabled: !!activeConvId,
    refetchInterval: 5000,
  })

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const sendMut = useMutation({
    mutationFn: (content: string) => {
      if (activeConvId) return sendMessage(activeConvId, content)
      // Create a new conversation first
      return createConversation({ institution_id: '', subject: 'AI Advisor' }).then(conv => {
        setActiveConvId(conv.id)
        return sendMessage(conv.id, content)
      })
    },
    onSuccess: () => {
      setInput('')
      queryClient.invalidateQueries({ queryKey: ['messages', activeConvId] })
      queryClient.invalidateQueries({ queryKey: ['conversations'] })
    },
  })

  const handleSend = () => {
    const trimmed = input.trim()
    if (!trimmed || sendMut.isPending) return
    sendMut.mutate(trimmed)
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const messageList: Message[] = messages ?? []

  return (
    <div className="flex flex-col h-full">
      <div className="px-6 py-3 border-b border-gray-200 bg-white">
        <h1 className="text-lg font-semibold">AI Advisor</h1>
      </div>

      <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
        {messagesLoading ? (
          <div className="space-y-4">
            {Array.from({ length: 3 }).map((_, i) => <Skeleton key={i} className="h-16 w-3/4" />)}
          </div>
        ) : messageList.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <div className="w-16 h-16 rounded-full bg-gray-100 flex items-center justify-center mb-4">
              <span className="text-2xl">🤖</span>
            </div>
            <h2 className="text-lg font-medium text-gray-700">Welcome to UniPaith!</h2>
            <p className="text-sm text-gray-500 mt-1 max-w-md">
              I'm your AI admissions advisor. Tell me about yourself and I'll help you find the best programs.
            </p>
          </div>
        ) : (
          messageList.map(msg => {
            const isOwn = msg.sender_type === 'student'
            return (
              <div key={msg.id} className={`flex ${isOwn ? 'justify-end' : 'justify-start'}`}>
                <div className={`flex gap-2 max-w-[80%] ${isOwn ? 'flex-row-reverse' : ''}`}>
                  <Avatar
                    name={isOwn ? (user?.email || '?') : 'AI'}
                    size="sm"
                  />
                  <div>
                    <div className={`px-4 py-2 rounded-2xl text-sm whitespace-pre-wrap ${
                      isOwn
                        ? 'bg-gray-900 text-white rounded-br-md'
                        : 'bg-gray-100 text-gray-800 rounded-bl-md'
                    }`}>
                      {msg.message_body}
                    </div>
                    <p className="text-[10px] text-gray-400 mt-1 px-1">
                      {formatRelative(msg.sent_at)}
                    </p>
                  </div>
                </div>
              </div>
            )
          })
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="px-6 py-3 border-t border-gray-200 bg-white">
        <div className="flex items-end gap-2">
          <button className="p-2 text-gray-400 hover:text-gray-600">
            <Paperclip size={18} />
          </button>
          <textarea
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Type a message..."
            rows={1}
            className="flex-1 resize-none border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-gray-900"
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || sendMut.isPending}
            className="p-2 bg-gray-900 text-white rounded-lg hover:bg-gray-800 disabled:opacity-50"
          >
            <ArrowUp size={18} />
          </button>
        </div>
        <div className="flex gap-2 mt-2">
          {QUICK_ACTIONS.map(action => (
            <button
              key={action}
              onClick={() => { setInput(action); }}
              className="px-3 py-1 text-xs bg-gray-100 text-gray-600 rounded-full hover:bg-gray-200"
            >
              {action}
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
