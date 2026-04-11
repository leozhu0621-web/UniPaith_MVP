import { useState, useEffect, useRef, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery, useMutation } from '@tanstack/react-query'
import { getOnboarding } from '../../api/students'
import { getMatches } from '../../api/matching'
import { listMyApplications } from '../../api/applications'
import { chatStudentAssistant } from '../../api/matching'
import { useAuthStore } from '../../stores/auth-store'
import { ArrowUp, Sparkles, ShieldCheck, AlertTriangle } from 'lucide-react'
import Avatar from '../../components/ui/Avatar'
import { formatRelative } from '../../utils/format'
import Skeleton from '../../components/ui/Skeleton'

type ChatMessage = {
  id: string
  sender_type: 'student' | 'assistant'
  message_body: string
  sent_at: string
}

export default function ChatPage() {
  const navigate = useNavigate()
  const user = useAuthStore(s => s.user)
  const [input, setInput] = useState('')
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([])
  const [sendError, setSendError] = useState<string | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // Context data for dynamic quick actions
  const { data: onboarding, isError: onboardingError } = useQuery({ queryKey: ['onboarding'], queryFn: getOnboarding })
  const { data: matches, isError: matchesError } = useQuery({
    queryKey: ['matches'],
    queryFn: () => getMatches(),
    enabled: (onboarding?.completion_percentage ?? 0) >= 80,
  })
  const { data: applications, isError: applicationsError } = useQuery({ queryKey: ['my-applications'], queryFn: listMyApplications })

  const completionPct = typeof onboarding?.completion_percentage === 'number' ? onboarding.completion_percentage : 0
  const matchesList: any[] = Array.isArray(matches) ? matches : []
  const applicationsList: any[] = Array.isArray(applications) ? applications : []
  const matchCount = matchesList.length
  const appCount = applicationsList.length
  const draftApps = applicationsList.filter((a: any) => a.status === 'draft').length

  // Dynamic quick actions based on profile state
  const quickActions = useMemo(() => {
    const actions: { label: string; action: string | (() => void) }[] = []

    if (completionPct < 80) {
      actions.push({ label: 'Complete my profile', action: () => navigate('/s/profile') })
    }
    if (completionPct < 50) {
      actions.push({ label: 'Calm next step', action: 'What is the calmest next step I should take to improve my profile?' })
    }
    if (matchCount > 0) {
      actions.push({ label: 'Explain my top match', action: 'Can you explain my top match in a reassuring way and what I can improve?' })
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
    actions.push({ label: 'Reduce stress now', action: 'I feel stressed about admissions. Give me a practical plan for this week.' })
    actions.push({ label: 'Help with essay', action: 'Can you help me brainstorm ideas for my personal statement?' })

    return actions.slice(0, 5)
  }, [completionPct, matchCount, appCount, draftApps, navigate])

  const messagesLoading = false

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [chatMessages])

  const sendMut = useMutation({
    mutationFn: (content: string) => chatStudentAssistant(content),
    onSuccess: (data) => {
      setInput('')
      setSendError(null)
      if (data?.reply) {
        const assistantMessage: ChatMessage = {
          id: `assistant-${Date.now()}`,
          sender_type: 'assistant',
          message_body: data.reply,
          sent_at: new Date().toISOString(),
        }
        setChatMessages(prev => [...prev, assistantMessage])
      }
    },
    onError: (err) => {
      setSendError(err instanceof Error ? err.message : 'Message failed to send. Please try again.')
    },
  })

  const handleSend = () => {
    const trimmed = input.trim()
    if (!trimmed || sendMut.isPending) return
    const studentMessage: ChatMessage = {
      id: `student-${Date.now()}`,
      sender_type: 'student',
      message_body: trimmed,
      sent_at: new Date().toISOString(),
    }
    setChatMessages(prev => [...prev, studentMessage])
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

  const messageList: ChatMessage[] = chatMessages

  return (
    <div className="flex flex-col h-full">
      {/* Header with context indicator */}
      <div className="px-6 py-3 border-b border-gray-200 bg-white flex items-center justify-between">
        <div className="flex items-center gap-2">
          <h1 className="text-lg font-semibold text-stone-700">Your AI Guide</h1>
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
        {(onboardingError || matchesError || applicationsError) && (
          <div className="rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-800 flex items-start gap-2">
            <AlertTriangle size={14} className="mt-0.5" />
            Some advisor context is temporarily unavailable, but chat is fully usable.
          </div>
        )}
        {messagesLoading ? (
          <div className="space-y-4">
            {Array.from({ length: 3 }).map((_, i) => <Skeleton key={i} className="h-16 w-3/4" />)}
          </div>
        ) : messageList.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <div className="w-16 h-16 rounded-full bg-gray-100 flex items-center justify-center mb-4">
              <Sparkles size={28} className="text-amber-500" />
            </div>
            <h2 className="text-lg font-medium text-brand-slate-600">You are not doing this alone.</h2>
            <p className="text-sm text-gray-500 mt-1 max-w-md">
              I am your counselor-style AI guide. I will help you prioritize calmly,
              explain options clearly, and turn uncertainty into next steps.
            </p>
            <div className="mt-3 flex items-center gap-2 text-xs text-gray-500 bg-gray-100 rounded-full px-3 py-1">
              <ShieldCheck size={13} className="text-gray-600" />
              Recommendations include explanation and confidence context.
            </div>
          </div>
        ) : (
          messageList.map(msg => {
            const isOwn = msg.sender_type === 'student'
            return (
              <div key={msg.id} className={`flex ${isOwn ? 'justify-end' : 'justify-start'}`}>
                <div className={`flex gap-2 max-w-[80%] ${isOwn ? 'flex-row-reverse' : ''}`}>
                  <Avatar
                    name={isOwn ? (user?.email || '?') : 'Counselor'}
                    size="sm"
                  />
                  <div>
                    <div className={`px-4 py-2 rounded-2xl text-sm whitespace-pre-wrap ${
                      isOwn
                        ? 'bg-brand-slate-700 text-white rounded-br-md'
                        : 'bg-white shadow-sm text-brand-slate-700 rounded-bl-md'
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
          <textarea
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Type a message..."
            rows={1}
            className="flex-1 resize-none border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-slate-700"
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || sendMut.isPending}
            className="p-2 bg-brand-slate-700 text-white rounded-lg hover:bg-brand-slate-600 disabled:opacity-50"
          >
            <ArrowUp size={18} />
          </button>
        </div>
        {sendError && (
          <p className="text-xs text-red-600 mt-2">
            {sendError} You can retry now without losing your message.
          </p>
        )}
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
