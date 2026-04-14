import { useState, useEffect, useRef } from 'react'
import { useSearchParams } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import { chatStudentAssistant } from '../../api/matching'
import { useCounselorStore } from '../../stores/counselor-store'
import { useAuthStore } from '../../stores/auth-store'
import Avatar from '../../components/ui/Avatar'
import { ArrowUp, Sparkles, Compass, BookOpen, Target, Lightbulb, Plus, Clock } from 'lucide-react'

const PROMPT_CATEGORIES = [
  {
    label: 'Self-Discovery',
    icon: Compass,
    prompts: [
      'Help me understand my strengths and what makes me unique',
      'What fields of study match my interests and background?',
      'Am I ready for graduate school? What should I work on?',
    ],
  },
  {
    label: 'Preparation',
    icon: BookOpen,
    prompts: [
      'Review my essay draft and give me feedback',
      'How can I strengthen my resume for applications?',
      'What test scores do programs in my field expect?',
    ],
  },
  {
    label: 'Targeted Help',
    icon: Target,
    prompts: [
      'Compare my saved programs and help me decide',
      "What's missing from my application checklist?",
      'Help me write a compelling personal statement',
    ],
  },
  {
    label: 'Career & Goals',
    icon: Lightbulb,
    prompts: [
      'What careers align with my interests?',
      'Help me articulate my academic goals clearly',
      'What experiences should I gain before applying?',
    ],
  },
]

export default function CounselorHomePage() {
  const [searchParams] = useSearchParams()
  const user = useAuthStore(s => s.user)
  const { messages, addMessage } = useCounselorStore()
  const [input, setInput] = useState('')
  const endRef = useRef<HTMLDivElement>(null)
  const prefillDone = useRef(false)

  // Prefill support
  useEffect(() => {
    const prefill = searchParams.get('prefill')
    if (prefill && !prefillDone.current) {
      prefillDone.current = true
      setInput(prefill)
    }
  }, [searchParams])

  const sendMut = useMutation({
    mutationFn: (content: string) => chatStudentAssistant(content),
    onError: () => {
      addMessage({
        id: `err-${Date.now()}`,
        sender_type: 'assistant',
        message_body: "Sorry, I had a brief hiccup. Could you try that again?",
        sent_at: new Date().toISOString(),
      })
    },
  })

  useEffect(() => {
    if (sendMut.data?.reply) {
      addMessage({
        id: `a-${Date.now()}`,
        sender_type: 'assistant',
        message_body: sendMut.data!.reply,
        sent_at: new Date().toISOString(),
      })
    }
  }, [sendMut.data, addMessage])

  useEffect(() => { endRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [messages])

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

  const handlePrompt = (prompt: string) => setInput(prompt)
  const name = user?.email?.split('@')[0] || ''

  return (
    <div className="flex h-full">
      {/* Left: Chat History + Prompts (ChatGPT-style sidebar) */}
      <aside className="w-64 flex-shrink-0 border-r border-divider bg-white overflow-y-auto hidden lg:flex flex-col">
        {/* New chat button */}
        <div className="p-3 border-b border-divider">
          <button className="w-full flex items-center gap-2 px-3 py-2 text-xs font-medium text-student-ink bg-student-mist hover:bg-student-moss rounded-lg transition-colors">
            <Plus size={14} /> New Conversation
          </button>
        </div>

        {/* Chat history */}
        {messages.length > 0 && (
          <div className="px-3 pt-3 pb-2">
            <p className="text-[10px] font-semibold text-student-text uppercase tracking-wider mb-2 px-1">
              <Clock size={10} className="inline mr-1" />Recent
            </p>
            <div className="space-y-0.5">
              {/* Show first message of each "conversation" (student messages as titles) */}
              {messages
                .filter(m => m.sender_type === 'student')
                .slice(-10)
                .reverse()
                .map(m => (
                  <div
                    key={m.id}
                    className="px-2.5 py-1.5 text-[11px] text-student-text hover:text-student-ink hover:bg-student-mist rounded-lg cursor-pointer transition-colors truncate"
                  >
                    {m.message_body.slice(0, 50)}{m.message_body.length > 50 ? '...' : ''}
                  </div>
                ))
              }
            </div>
          </div>
        )}

        {/* Prompt suggestions */}
        <div className="flex-1 px-3 pt-3 space-y-4 overflow-y-auto">
          {PROMPT_CATEGORIES.map(cat => (
            <div key={cat.label}>
              <div className="flex items-center gap-1.5 mb-1.5">
                <cat.icon size={11} className="text-student" />
                <p className="text-[10px] font-semibold text-student-ink uppercase tracking-wider">{cat.label}</p>
              </div>
              <div className="space-y-0.5">
                {cat.prompts.map((p, i) => (
                  <button
                    key={i}
                    onClick={() => handlePrompt(p)}
                    className="w-full text-left px-2.5 py-1.5 text-[11px] text-student-text hover:text-student-ink hover:bg-student-mist rounded-lg transition-colors leading-relaxed"
                  >
                    {p}
                  </button>
                ))}
              </div>
            </div>
          ))}
        </div>
      </aside>

      {/* Right: Chat area */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-6 py-6">
          <div className="max-w-2xl mx-auto space-y-4">
            {messages.length === 0 && (
              <>
                <div className="flex gap-3">
                  <div className="w-9 h-9 rounded-full bg-gold-soft flex items-center justify-center flex-shrink-0 mt-0.5">
                    <Sparkles size={16} className="text-gold" />
                  </div>
                  <div className="bg-white rounded-2xl rounded-tl-md px-4 py-3 shadow-sm border border-divider max-w-lg">
                    <p className="text-sm text-student-ink leading-relaxed">
                      Hi{name ? ` ${name}` : ''}! I'm your private counselor. I'm here to help you discover your path, prepare your applications, and make sense of your options. What would you like to work on?
                    </p>
                  </div>
                </div>
                {/* Mobile prompt suggestions */}
                <div className="flex flex-wrap gap-2 lg:hidden">
                  {PROMPT_CATEGORIES.flatMap(c => c.prompts).slice(0, 4).map((p, i) => (
                    <button
                      key={i}
                      onClick={() => handlePrompt(p)}
                      className="px-3 py-1.5 text-xs rounded-full bg-student-mist text-student-text hover:text-student-ink transition-colors"
                    >
                      {p.length > 40 ? p.slice(0, 40) + '...' : p}
                    </button>
                  ))}
                </div>
              </>
            )}

            {messages.map(msg => (
              <div key={msg.id} className={`flex gap-3 ${msg.sender_type === 'student' ? 'justify-end' : ''}`}>
                {msg.sender_type === 'assistant' && (
                  <div className="w-9 h-9 rounded-full bg-gold-soft flex items-center justify-center flex-shrink-0 mt-0.5">
                    <Sparkles size={16} className="text-gold" />
                  </div>
                )}
                <div className={`max-w-lg px-4 py-3 rounded-2xl text-sm leading-relaxed ${
                  msg.sender_type === 'student'
                    ? 'bg-student text-white rounded-br-md'
                    : 'bg-white shadow-sm border border-divider text-student-ink rounded-bl-md'
                }`}>
                  {msg.message_body}
                </div>
                {msg.sender_type === 'student' && <Avatar name={user?.email || '?'} size="sm" />}
              </div>
            ))}

            {sendMut.isPending && (
              <div className="flex gap-3">
                <div className="w-9 h-9 rounded-full bg-gold-soft flex items-center justify-center flex-shrink-0">
                  <Sparkles size={16} className="text-gold" />
                </div>
                <div className="bg-white rounded-2xl rounded-tl-md px-4 py-3 shadow-sm border border-divider">
                  <div className="flex gap-1">
                    <span className="w-2 h-2 bg-student-text/30 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                    <span className="w-2 h-2 bg-student-text/30 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                    <span className="w-2 h-2 bg-student-text/30 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                  </div>
                </div>
              </div>
            )}
            <div ref={endRef} />
          </div>
        </div>

        {/* Input */}
        <div className="px-6 py-4 border-t border-divider bg-white">
          <div className="max-w-2xl mx-auto flex items-center gap-2">
            <textarea
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend() } }}
              placeholder="Ask your counselor anything..."
              rows={1}
              className="flex-1 resize-none border border-stone rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-student bg-offwhite"
            />
            <button
              onClick={handleSend}
              disabled={!input.trim() || sendMut.isPending}
              className="p-2.5 bg-student text-white rounded-xl hover:bg-student-hover disabled:opacity-30 transition-all"
            >
              <ArrowUp size={18} />
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
