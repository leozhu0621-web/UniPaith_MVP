import { useState, useEffect, useRef, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getConversations, getMessages, sendMessage, createConversation } from '../../api/messaging'
import { getOnboarding } from '../../api/students'
import { getMatches } from '../../api/matching'
import { listMyApplications } from '../../api/applications'
import { useAuthStore } from '../../stores/auth-store'
import { Paperclip, ArrowUp, Sparkles } from 'lucide-react'
import Avatar from '../../components/ui/Avatar'
import { formatRelative } from '../../utils/format'
import Skeleton from '../../components/ui/Skeleton'
import type { Message } from '../../types'

export default function ChatPage() {
  const navigate = useNavigate()
  const user = useAuthStore(s => s.user)
  const queryClient = useQueryClient()
  const [input, setInput] = useState('')
  const [activeConvId, setActiveConvId] = useState<string | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // Context data for dynamic quick actions
  const { data: onboarding } = useQuery({ queryKey: ['onboarding'], queryFn: getOnboarding })
  const { data: matches } = useQuery({ queryKey: ['matches'], queryFn: () => getMatches(), enabled: (onboarding?.completion_percentage ?? 0) >= 80 })
  const { data: applications } = useQuery({ queryKey: ['my-applications'], queryFn: listMyApplications })

  const completionPct = onboarding?.completion_percentage ?? 0
  const matchCount = (matches ?? []).length
  const appCount = (applications ?? []).length
  const draftApps = (applications ?? []).filter((a: any) => a.status === 'draft').length

  // Dynamic quick actions based on profile state
  const quickActions = useMemo(() => {
    const actions: { label: string; action: string | (() => void) }[] = []

    if (completionPct < 80) {
      actions.push({ label: 'Complete my profile', action: () => navigate('/s/profile') })
    }
    if (completionPct < 50) {
      actions.push({ label: 'What should I fill in next?', action: 'What should I add to my profile next to improve my matches?' })
    }
    if (matchCount > 0) {
      actions.push({ label: 'Explain my top match', action: 'Can you explain why my top match is a good fit for me?' })
    }
    if (matchCount === 0 && completionPct >= 80) {
      actions.push({ label: 'Why no matches yet?', action: 'I completed my profile but have no matches yet. What should I do?' })
    }
    if (draftApps > 0) {
      actions.push({ label: 'Help with my application', action: 'I have a draft application. Can you help me prepare it for submission?' })
    }
    if (appCount > 0) {
      actions.push({ label: 'Application status update', action: 'Can you give me an overview of my application statuses?' })
    }

    // Always available
    actions.push({ label: 'Help with essay', action: 'Can you help me brainstorm ideas for my personal statement?' })
    actions.push({ label: 'Find programs', action: 'Help me find programs that match my interests and qualifications.' })

    return actions.slice(0, 5)
  }, [completionPct, matchCount, appCount, draftApps, navigate])

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

  const handleQuickAction = (action: string | (() => void)) => {
    if (typeof action === 'function') {
      action()
    } else {
      setInput(action)
    }
  }

  const messageList: Message[] = messages ?? []

  return (
    <div className="flex flex-col h-full">
      {/* Header with context indicator */}
      <div className="px-6 py-3 border-b border-gray-200 bg-white flex items-center justify-between">
        <div className="flex items-center gap-2">
          <h1 className="text-lg font-semibold">AI Advisor</h1>
          <Sparkles size={16} className="text-amber-500" />
        </div>
        <div className="flex items-center gap-3 text-xs text-gray-500">
          <span>Profile: {completionPct}%</span>
          <span className="w-px h-3 bg-gray-300" />
          <span>{matchCount} matches</span>
          <span className="w-px h-3 bg-gray-300" />
          <span>{appCount} apps</span>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
        {messagesLoading ? (
          <div className="space-y-4">
            {Array.from({ length: 3 }).map((_, i) => <Skeleton key={i} className="h-16 w-3/4" />)}
          </div>
        ) : messageList.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <div className="w-16 h-16 rounded-full bg-gray-100 flex items-center justify-center mb-4">
              <Sparkles size={28} className="text-amber-500" />
            </div>
            <h2 className="text-lg font-medium text-gray-700">Welcome to UniPaith!</h2>
            <p className="text-sm text-gray-500 mt-1 max-w-md">
              I'm your AI admissions advisor. I can see your profile ({completionPct}% complete),
              {matchCount > 0 ? ` ${matchCount} matches,` : ''} and {appCount} applications.
              How can I help?
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
        <div className="flex gap-2 mt-2 overflow-x-auto">
          {quickActions.map((qa, i) => (
            <button
              key={i}
              onClick={() => handleQuickAction(qa.action)}
              className="px-3 py-1 text-xs bg-gray-100 text-gray-600 rounded-full hover:bg-gray-200 whitespace-nowrap flex-shrink-0"
            >
              {qa.label}
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
