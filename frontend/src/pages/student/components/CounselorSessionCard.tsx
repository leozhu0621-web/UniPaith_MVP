import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import { chatStudentAssistant } from '../../../api/matching'
import { Sparkles, ArrowUp, ArrowRight, User, Search, FileText } from 'lucide-react'

interface Props {
  guidanceText: string
  completionPct: number
  matchCount?: number
  savedCount: number
  appCount: number
}

export default function CounselorSessionCard({
  guidanceText,
  completionPct,
  savedCount,
  appCount,
}: Props) {
  const navigate = useNavigate()
  const [input, setInput] = useState('')
  const [response, setResponse] = useState('')

  const chatMut = useMutation({
    mutationFn: (msg: string) => chatStudentAssistant(msg),
    onSuccess: (data) => {
      setResponse(data.message_body || data.message || 'Let me think about that...')
    },
    onError: () => {
      setResponse("I'm having trouble connecting right now. Try the full counselor chat instead.")
    },
  })

  const handleSend = () => {
    const trimmed = input.trim()
    if (!trimmed || chatMut.isPending) return
    chatMut.mutate(trimmed)
    setInput('')
  }

  // Smart action suggestions based on journey stage
  const actions: { label: string; to: string; icon: typeof Sparkles }[] = []
  if (completionPct < 80) {
    actions.push({ label: 'Continue your story', to: '/s/profile', icon: User })
  }
  if (completionPct >= 50) {
    actions.push({ label: 'Explore programs', to: '/s/discover', icon: Search })
  }
  if (savedCount > 0 && appCount === 0) {
    actions.push({ label: 'Start applying', to: '/s/applications', icon: FileText })
  }
  if (actions.length === 0) {
    actions.push({ label: 'Explore programs', to: '/s/discover', icon: Search })
  }

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
      {/* Counselor header */}
      <div className="flex items-start gap-3 p-5 pb-3">
        <div className="w-10 h-10 rounded-full bg-gold-pale flex items-center justify-center flex-shrink-0">
          <Sparkles size={18} className="text-gold" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <h3 className="text-sm font-semibold text-student-ink">Your AI Counselor</h3>
            <span className="text-[10px] text-gray-400 font-medium">Personalized guidance</span>
          </div>
          <p className="text-sm text-gray-600 leading-relaxed">{guidanceText}</p>
        </div>
      </div>

      {/* Inline response */}
      {response && (
        <div className="mx-5 mb-3 px-4 py-3 bg-blue-50 border border-blue-100 rounded-xl">
          <p className="text-sm text-blue-800 leading-relaxed">{response}</p>
        </div>
      )}

      {/* Inline chat input */}
      <div className="px-5 pb-3">
        <div className="flex items-center gap-2 bg-gray-50 rounded-xl border border-gray-200 px-3 py-2">
          <input
            type="text"
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleSend()}
            placeholder="Ask your counselor anything..."
            className="flex-1 bg-transparent text-sm outline-none placeholder:text-gray-400"
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || chatMut.isPending}
            className="w-7 h-7 flex items-center justify-center rounded-lg bg-student text-white disabled:opacity-30 transition-opacity"
          >
            {chatMut.isPending ? (
              <span className="w-3 h-3 border-2 border-white border-t-transparent rounded-full animate-spin" />
            ) : (
              <ArrowUp size={14} />
            )}
          </button>
        </div>
      </div>

      {/* Action suggestions */}
      <div className="flex items-center gap-2 px-5 pb-4">
        {actions.map(a => (
          <button
            key={a.to}
            onClick={() => navigate(a.to)}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-student bg-student-mist hover:bg-student-moss rounded-lg transition-colors"
          >
            <a.icon size={12} />
            {a.label}
            <ArrowRight size={10} />
          </button>
        ))}
        <button
          onClick={() => navigate('/s/chat')}
          className="ml-auto text-xs text-gray-400 hover:text-gray-600 transition-colors"
        >
          Full conversation &rarr;
        </button>
      </div>
    </div>
  )
}
