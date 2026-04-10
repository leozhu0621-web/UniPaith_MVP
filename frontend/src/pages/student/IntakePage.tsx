import { useState, useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import apiClient from '../../api/client'
import Card from '../../components/ui/Card'
import Badge from '../../components/ui/Badge'
import Button from '../../components/ui/Button'
import Avatar from '../../components/ui/Avatar'
import ProgressBar from '../../components/ui/ProgressBar'
import { useAuthStore } from '../../stores/auth-store'
import { Sparkles, ArrowUp, Check, ArrowRight } from 'lucide-react'

const intakeChat = (message: string) =>
  apiClient.post('/students/me/intake/chat', { message }, { timeout: 120_000 }).then(r => r.data)

interface ChatMsg {
  id: string
  role: 'student' | 'assistant'
  text: string
  extracted?: Record<string, string>
}

const INITIAL_QUESTIONS = [
  "Hi! Let's get to know you. What's your name and where are you from?",
  "What field are you interested in studying?",
  "What degree level are you looking for? (Bachelor's, Master's, PhD)",
  "Do you have any budget or location preferences?",
]

export default function IntakePage() {
  const user = useAuthStore(s => s.user)
  const navigate = useNavigate()
  const [messages, setMessages] = useState<ChatMsg[]>([
    { id: 'welcome', role: 'assistant', text: INITIAL_QUESTIONS[0] },
  ])
  const [input, setInput] = useState('')
  const [completionPct, setCompletionPct] = useState(0)
  const [questionIdx, setQuestionIdx] = useState(0)
  const endRef = useRef<HTMLDivElement>(null)

  const chatMut = useMutation({
    mutationFn: intakeChat,
    onSuccess: (data) => {
      const nextIdx = questionIdx + 1
      const nextQ = data.next_question || (nextIdx < INITIAL_QUESTIONS.length ? INITIAL_QUESTIONS[nextIdx] : "Anything else you'd like to share?")

      const assistantMsg: ChatMsg = {
        id: `a-${Date.now()}`,
        role: 'assistant',
        text: nextQ,
        extracted: data.extracted_fields,
      }
      setMessages(prev => [...prev, assistantMsg])
      setCompletionPct(data.completion_pct || 0)
      setQuestionIdx(nextIdx)
    },
  })

  const handleSend = () => {
    const trimmed = input.trim()
    if (!trimmed || chatMut.isPending) return
    setMessages(prev => [...prev, { id: `s-${Date.now()}`, role: 'student', text: trimmed }])
    setInput('')
    chatMut.mutate(trimmed)
  }

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  return (
    <div className="flex flex-col h-full">
      <div className="px-6 py-3 border-b border-gray-100 bg-white">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Sparkles size={18} className="text-amber-500" />
            <h1 className="text-lg font-semibold text-stone-700">Quick Start</h1>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-xs text-gray-500">{completionPct}% complete</span>
            <div className="w-32"><ProgressBar value={completionPct} /></div>
            <Button size="sm" variant="secondary" onClick={() => navigate('/s/profile')}>
              Skip to Profile <ArrowRight size={12} className="ml-1" />
            </Button>
          </div>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4 bg-stone-50">
        {messages.map(msg => {
          const isOwn = msg.role === 'student'
          return (
            <div key={msg.id}>
              <div className={`flex ${isOwn ? 'justify-end' : 'justify-start'}`}>
                <div className={`flex gap-2 max-w-[80%] ${isOwn ? 'flex-row-reverse' : ''}`}>
                  <Avatar name={isOwn ? (user?.email || '?') : 'AI'} size="sm" />
                  <div className={`px-4 py-2 rounded-2xl text-sm ${isOwn ? 'bg-stone-700 text-white rounded-br-md' : 'bg-white shadow-sm text-stone-700 rounded-bl-md'}`}>
                    {msg.text}
                  </div>
                </div>
              </div>
              {msg.extracted && Object.keys(msg.extracted).length > 0 && (
                <div className="ml-12 mt-2">
                  <Card className="p-3 bg-emerald-50 border-emerald-200">
                    <p className="text-xs font-medium text-emerald-700 mb-1.5">
                      <Check size={12} className="inline mr-1" />Extracted from your answer:
                    </p>
                    <div className="flex flex-wrap gap-2">
                      {Object.entries(msg.extracted).map(([k, v]) => (
                        <Badge key={k} variant="success" size="sm">
                          {k.replace(/_/g, ' ')}: {String(v)}
                        </Badge>
                      ))}
                    </div>
                  </Card>
                </div>
              )}
            </div>
          )
        })}
        {chatMut.isPending && (
          <div className="flex justify-start">
            <div className="px-4 py-3 rounded-2xl bg-white shadow-sm text-gray-400 text-sm animate-pulse">
              Thinking...
            </div>
          </div>
        )}
        <div ref={endRef} />
      </div>

      <div className="px-6 py-3 border-t border-gray-100 bg-white">
        <div className="flex items-end gap-2">
          <textarea
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend() } }}
            placeholder="Type your answer..."
            rows={1}
            className="flex-1 resize-none border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-stone-700"
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || chatMut.isPending}
            className="p-2 bg-stone-700 text-white rounded-lg hover:bg-stone-600 disabled:opacity-50"
          >
            <ArrowUp size={18} />
          </button>
        </div>
      </div>
    </div>
  )
}
