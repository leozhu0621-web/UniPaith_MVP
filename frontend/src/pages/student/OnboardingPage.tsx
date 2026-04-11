import { useState, useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import apiClient from '../../api/client'
import { useAuthStore } from '../../stores/auth-store'
import Button from '../../components/ui/Button'
import { Sparkles, ArrowUp, Check, ArrowRight, SkipForward } from 'lucide-react'

const intakeChat = (message: string) =>
  apiClient.post('/students/me/intake/chat', { message }, { timeout: 120_000 }).then(r => r.data)

interface ChatMsg {
  id: string
  role: 'student' | 'ai'
  text: string
  extracted?: Record<string, string>
}

const UNDERSTANDING_MILESTONES = [
  { pct: 0, label: 'Just met you', emoji: '👋' },
  { pct: 15, label: 'Getting a sense', emoji: '🌱' },
  { pct: 30, label: 'Starting to see you', emoji: '🔍' },
  { pct: 50, label: 'Forming a picture', emoji: '🎨' },
  { pct: 70, label: 'Understanding deeply', emoji: '💡' },
  { pct: 85, label: 'Almost there', emoji: '✨' },
  { pct: 100, label: 'Ready to guide you', emoji: '🚀' },
]

function UnderstandingMeter({ pct }: { pct: number }) {
  const milestone = [...UNDERSTANDING_MILESTONES].reverse().find(m => pct >= m.pct) || UNDERSTANDING_MILESTONES[0]

  return (
    <div className="flex items-center gap-3">
      <div className="flex-1 h-1.5 bg-white/20 rounded-full overflow-hidden">
        <div
          className="h-full bg-gradient-to-r from-amber-400 to-emerald-400 rounded-full transition-all duration-1000 ease-out"
          style={{ width: `${Math.min(pct, 100)}%` }}
        />
      </div>
      <span className="text-xs text-white/70 whitespace-nowrap">
        {milestone.emoji} {milestone.label}
      </span>
    </div>
  )
}

export default function OnboardingPage() {
  const navigate = useNavigate()
  useAuthStore()
  const [messages, setMessages] = useState<ChatMsg[]>([])
  const [input, setInput] = useState('')
  const [understanding, setUnderstanding] = useState(0)
  const [extractedTotal, setExtractedTotal] = useState<Record<string, string>>({})
  const [showTransition, setShowTransition] = useState(false)
  const endRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)
  const [started, setStarted] = useState(false)

  const chatMut = useMutation({
    mutationFn: intakeChat,
    onSuccess: (data) => {
      const extracted = data.extracted_fields || {}
      setExtractedTotal(prev => {
        const newTotal = { ...prev, ...extracted }
        const newPct = data.completion_pct || Math.min(Object.keys(newTotal).length * 12, 95)
        setUnderstanding(newPct)
        return newTotal
      })

      const aiMsg: ChatMsg = {
        id: `ai-${Date.now()}`,
        role: 'ai',
        text: data.next_question || "Tell me more about what excites you.",
        extracted: Object.keys(extracted).length > 0 ? extracted : undefined,
      }
      setMessages(prev => [...prev, aiMsg])

      if (newPct >= 60) {
        setTimeout(() => setShowTransition(true), 2000)
      }
    },
    onError: () => {
      setMessages(prev => [...prev, {
        id: `ai-err-${Date.now()}`,
        role: 'ai',
        text: "Sorry, I had a brief hiccup. Could you try sending that again?",
      }])
    },
  })

  const handleSend = () => {
    const trimmed = input.trim()
    if (!trimmed || chatMut.isPending) return
    setMessages(prev => [...prev, { id: `s-${Date.now()}`, role: 'student', text: trimmed }])
    setInput('')
    chatMut.mutate(trimmed)
  }

  const handleStart = () => {
    setStarted(true)
    setMessages([{
      id: 'welcome',
      role: 'ai',
      text: "Hi! I'm your AI guide on UniPaith. Instead of filling out forms, let's just have a conversation. Tell me a little about yourself — your name, where you're from, and what brings you here today.",
    }])
    setTimeout(() => inputRef.current?.focus(), 300)
  }

  const handleSkip = () => {
    navigate('/s/profile')
  }

  const handleTransition = () => {
    navigate('/s/profile')
  }

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  if (!started) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-stone-800 via-stone-900 to-stone-950 flex items-center justify-center p-6">
        <div className="max-w-lg text-center">
          <div className="w-20 h-20 rounded-full bg-amber-500/20 flex items-center justify-center mx-auto mb-6">
            <Sparkles size={36} className="text-amber-400" />
          </div>
          <h1 className="text-3xl font-bold text-white mb-3">
            Welcome to UniPaith
          </h1>
          <p className="text-lg text-white/70 mb-2">
            Let's discover who you are and where you belong.
          </p>
          <p className="text-sm text-white/50 mb-8">
            No forms. No checkboxes. Just a conversation with your AI guide.
            Everything you share helps me find programs where you'll truly thrive.
          </p>
          <div className="space-y-3">
            <Button onClick={handleStart} className="w-full bg-amber-500 hover:bg-amber-600 text-stone-900 font-semibold py-3">
              <Sparkles size={18} className="mr-2" />
              Start My Journey
            </Button>
            <button
              onClick={handleSkip}
              className="text-sm text-white/40 hover:text-white/60 flex items-center gap-1 mx-auto"
            >
              <SkipForward size={14} /> I prefer filling forms manually
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-stone-800 via-stone-900 to-stone-950 flex flex-col">
      {/* Header with understanding meter */}
      <div className="px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-full bg-amber-500/20 flex items-center justify-center">
            <Sparkles size={16} className="text-amber-400" />
          </div>
          <span className="text-sm font-medium text-white/80">UniPaith AI</span>
        </div>
        <div className="flex-1 max-w-xs mx-4">
          <UnderstandingMeter pct={understanding} />
        </div>
        <button
          onClick={handleSkip}
          className="text-xs text-white/30 hover:text-white/50 flex items-center gap-1"
        >
          <SkipForward size={12} /> Skip to forms
        </button>
      </div>

      {/* Chat area */}
      <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4 max-w-2xl mx-auto w-full">
        {messages.map(msg => {
          const isAi = msg.role === 'ai'
          return (
            <div key={msg.id}>
              <div className={`flex ${isAi ? 'justify-start' : 'justify-end'}`}>
                <div className={`max-w-[85%] px-4 py-3 rounded-2xl text-sm leading-relaxed ${
                  isAi
                    ? 'bg-white/10 text-white/90 rounded-bl-md'
                    : 'bg-amber-500/90 text-stone-900 rounded-br-md'
                }`}>
                  {msg.text}
                </div>
              </div>
              {msg.extracted && Object.keys(msg.extracted).length > 0 && (
                <div className={`mt-2 ${isAi ? 'ml-0' : 'mr-0'}`}>
                  <div className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-emerald-500/10 rounded-full">
                    <Check size={12} className="text-emerald-400" />
                    <span className="text-xs text-emerald-300">
                      Understood: {Object.entries(msg.extracted).map(([k, v]) => `${k.replace(/_/g, ' ')} → ${v}`).join(', ')}
                    </span>
                  </div>
                </div>
              )}
            </div>
          )
        })}

        {chatMut.isPending && (
          <div className="flex justify-start">
            <div className="px-4 py-3 rounded-2xl rounded-bl-md bg-white/10">
              <div className="flex gap-1">
                <span className="w-2 h-2 bg-white/30 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                <span className="w-2 h-2 bg-white/30 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                <span className="w-2 h-2 bg-white/30 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
            </div>
          </div>
        )}

        {showTransition && (
          <div className="text-center py-6">
            <div className="inline-block bg-emerald-500/20 rounded-2xl px-6 py-4">
              <p className="text-emerald-300 font-medium mb-2">
                ✨ I have a good understanding of who you are now.
              </p>
              <p className="text-sm text-white/60 mb-3">
                I've pre-filled your profile with everything we discussed.
                Let's review it together — you can add more details anytime.
              </p>
              <Button onClick={handleTransition} className="bg-emerald-500 hover:bg-emerald-600 text-white">
                Review My Profile <ArrowRight size={14} className="ml-1" />
              </Button>
            </div>
          </div>
        )}

        <div ref={endRef} />
      </div>

      {/* Input */}
      {!showTransition && (
        <div className="px-6 py-4 max-w-2xl mx-auto w-full">
          <div className="flex items-end gap-2">
            <textarea
              ref={inputRef}
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend() } }}
              placeholder="Type freely — there are no wrong answers..."
              rows={1}
              className="flex-1 resize-none bg-white/10 border border-white/10 rounded-xl px-4 py-3 text-sm text-white placeholder-white/30 focus:outline-none focus:ring-2 focus:ring-amber-500/50"
            />
            <button
              onClick={handleSend}
              disabled={!input.trim() || chatMut.isPending}
              className="p-3 bg-amber-500 text-stone-900 rounded-xl hover:bg-amber-400 disabled:opacity-30 transition-colors"
            >
              <ArrowUp size={18} />
            </button>
          </div>
          <p className="text-[10px] text-white/20 text-center mt-2">
            Everything you share is private and helps your AI guide find better matches
          </p>
        </div>
      )}
    </div>
  )
}
