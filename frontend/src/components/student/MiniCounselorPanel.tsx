import { useState, useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import { chatStudentAssistant } from '../../api/matching'
import { useCounselorStore } from '../../stores/counselor-store'
import { useAuthStore } from '../../stores/auth-store'
import Avatar from '../ui/Avatar'
import { ArrowUp, Sparkles, X, Maximize2 } from 'lucide-react'

export default function MiniCounselorPanel() {
  const navigate = useNavigate()
  const user = useAuthStore(s => s.user)
  const { messages, addMessage, isMinimized, setMinimized, pendingPrompt, clearPendingPrompt } = useCounselorStore()
  const [input, setInput] = useState('')
  const endRef = useRef<HTMLDivElement>(null)

  const sendMut = useMutation({
    mutationFn: (content: string) => chatStudentAssistant(content),
    onError: () => {
      addMessage({
        id: `err-${Date.now()}`,
        sender_type: 'assistant',
        message_body: "Sorry, had a hiccup. Try again?",
        sent_at: new Date().toISOString(),
      })
    },
  })

  useEffect(() => {
    if (sendMut.data?.reply) {
      addMessage({
        id: `a-${Date.now()}`,
        sender_type: 'assistant',
        message_body: sendMut.data.reply,
        sent_at: new Date().toISOString(),
      })
    }
  }, [sendMut.data, addMessage])

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSend = () => {
    const trimmed = input.trim()
    if (!trimmed || sendMut.isPending) return
    addMessage({
      id: `s-${Date.now()}`,
      sender_type: 'student',
      message_body: trimmed,
      sent_at: new Date().toISOString(),
    })
    sendMut.mutate(trimmed)
    setInput('')
  }

  // Handle pre-filled prompts from in-page "Ask Counselor" CTAs (e.g., the
  // program detail page). When another component sets pendingPrompt, pick it
  // up, send as a student message, and clear the store flag.
  useEffect(() => {
    if (!pendingPrompt || sendMut.isPending) return
    const text = pendingPrompt
    clearPendingPrompt()
    addMessage({
      id: `s-${Date.now()}`,
      sender_type: 'student',
      message_body: text,
      sent_at: new Date().toISOString(),
    })
    sendMut.mutate(text)
  }, [pendingPrompt, sendMut, addMessage, clearPendingPrompt])

  if (isMinimized) return null

  return (
    <div className="flex flex-col h-full bg-white border-r border-divider">
      {/* Header */}
      <div className="flex items-center justify-between px-3 py-2.5 border-b border-divider flex-shrink-0">
        <div className="flex items-center gap-2">
          <Sparkles size={14} className="text-gold" />
          <span className="text-xs font-semibold text-student-ink">Counselor</span>
        </div>
        <div className="flex items-center gap-1">
          <button
            onClick={() => navigate('/s')}
            className="p-1 rounded hover:bg-student-mist text-student-text hover:text-student-ink transition-colors"
            title="Open full view"
          >
            <Maximize2 size={12} />
          </button>
          <button
            onClick={() => setMinimized(true)}
            className="p-1 rounded hover:bg-student-mist text-student-text hover:text-student-ink transition-colors"
            title="Hide counselor"
          >
            <X size={12} />
          </button>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-3 py-2 space-y-2">
        {messages.length === 0 && (
          <p className="text-[10px] text-student-text text-center py-4">
            Ask your counselor anything while you browse.
          </p>
        )}
        {messages.slice(-20).map(msg => (
          <div key={msg.id} className={`flex gap-1.5 ${msg.sender_type === 'student' ? 'justify-end' : ''}`}>
            {msg.sender_type === 'assistant' && (
              <div className="w-5 h-5 rounded-full bg-gold-soft flex items-center justify-center flex-shrink-0 mt-0.5">
                <Sparkles size={8} className="text-gold" />
              </div>
            )}
            <div className={`max-w-[85%] px-2.5 py-1.5 rounded-xl text-[11px] leading-relaxed ${
              msg.sender_type === 'student'
                ? 'bg-student text-white rounded-br-sm'
                : 'bg-student-mist text-student-ink rounded-bl-sm'
            }`}>
              {msg.message_body.length > 150 ? msg.message_body.slice(0, 150) + '...' : msg.message_body}
            </div>
            {msg.sender_type === 'student' && (
              <Avatar name={user?.email || '?'} size="sm" />
            )}
          </div>
        ))}
        {sendMut.isPending && (
          <div className="flex gap-1.5">
            <div className="w-5 h-5 rounded-full bg-gold-soft flex items-center justify-center flex-shrink-0">
              <Sparkles size={8} className="text-gold" />
            </div>
            <div className="px-2.5 py-1.5 rounded-xl bg-student-mist">
              <div className="flex gap-0.5">
                <span className="w-1 h-1 bg-student-text/30 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                <span className="w-1 h-1 bg-student-text/30 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                <span className="w-1 h-1 bg-student-text/30 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
            </div>
          </div>
        )}
        <div ref={endRef} />
      </div>

      {/* Input */}
      <div className="px-3 py-2 border-t border-divider flex-shrink-0">
        <div className="flex items-center gap-1.5">
          <input
            type="text"
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend() } }}
            placeholder="Ask anything..."
            className="flex-1 text-[11px] border border-stone rounded-lg px-2.5 py-1.5 focus:outline-none focus:ring-1 focus:ring-student bg-offwhite"
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || sendMut.isPending}
            className="p-1.5 bg-student text-white rounded-lg hover:bg-student-hover disabled:opacity-30 transition-all"
          >
            <ArrowUp size={12} />
          </button>
        </div>
      </div>
    </div>
  )
}
