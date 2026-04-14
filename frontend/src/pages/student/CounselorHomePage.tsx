import { useState, useEffect, useRef, useMemo } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useQuery, useMutation } from '@tanstack/react-query'
import { getOnboarding, getNextStep } from '../../api/students'
import { getMatches, chatStudentAssistant } from '../../api/matching'
import { listMyApplications } from '../../api/applications'
import { listSaved } from '../../api/saved-lists'
import { useDeadlines } from '../../hooks/useDeadlines'
import { useAuthStore } from '../../stores/auth-store'
// format utils available if needed
import Avatar from '../../components/ui/Avatar'
import Badge from '../../components/ui/Badge'
import {
  ArrowUp, Sparkles, Calendar, Bookmark, Search,
  ChevronRight, Clock, GraduationCap,
} from 'lucide-react'
import { differenceInDays, parseISO } from 'date-fns'
import type { Application } from '../../types'

type ChatMessage = {
  id: string
  sender_type: 'student' | 'assistant'
  message_body: string
  sent_at: string
}

export default function CounselorHomePage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const user = useAuthStore(s => s.user)
  const [input, setInput] = useState('')
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([])
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const prefillHandled = useRef(false)

  // --- Data ---
  const { data: onboarding } = useQuery({ queryKey: ['onboarding'], queryFn: getOnboarding })
  const { data: nextStep } = useQuery({ queryKey: ['next-step'], queryFn: getNextStep })
  const { data: saved } = useQuery({ queryKey: ['saved'], queryFn: listSaved })
  const { data: matches } = useQuery({
    queryKey: ['matches'],
    queryFn: () => getMatches(),
    enabled: (onboarding?.completion_percentage ?? 0) >= 80,
  })
  const { data: applications } = useQuery({ queryKey: ['my-applications'], queryFn: listMyApplications })
  const { deadlines } = useDeadlines()

  const completionPct = onboarding?.completion_percentage ?? 0
  const matchCount = Array.isArray(matches) ? matches.length : 0
  const savedCount = Array.isArray(saved) ? saved.length : 0
  const appsList: Application[] = Array.isArray(applications) ? applications : []
  const draftApps = appsList.filter(a => a.status === 'draft')
  const activeApps = appsList.filter(a => a.status !== 'decision_made')
  const upcomingDeadlines = deadlines.slice(0, 5)

  // --- Prefill ---
  useEffect(() => {
    const prefill = searchParams.get('prefill')
    if (prefill && !prefillHandled.current) {
      prefillHandled.current = true
      setInput(prefill)
    }
  }, [searchParams])

  // --- Quick actions ---
  const quickActions = useMemo(() => {
    const actions: { label: string; action: string | (() => void) }[] = []
    if (completionPct < 80)
      actions.push({ label: 'Help me complete my profile', action: 'What should I add to my profile next to strengthen it?' })
    if (completionPct >= 80 && matchCount === 0)
      actions.push({ label: 'Find programs for me', action: 'Based on my profile, what programs would you recommend?' })
    if (matchCount > 0)
      actions.push({ label: 'Explain my top match', action: 'Can you explain my top match and why it fits me?' })
    if (draftApps.length > 0)
      actions.push({ label: 'Help with my application', action: 'Help me finish my draft application.' })
    if (savedCount > 0 && appsList.length === 0)
      actions.push({ label: 'Which should I apply to?', action: 'I have programs saved. Which should I apply to first and why?' })
    actions.push({ label: 'Help with my essay', action: 'Help me brainstorm ideas for my personal statement.' })
    actions.push({ label: 'What should I do next?', action: 'What is the most important thing I should focus on right now?' })
    return actions.slice(0, 4)
  }, [completionPct, matchCount, savedCount, draftApps.length, appsList.length])

  // --- Chat ---
  const sendMut = useMutation({
    mutationFn: (content: string) => chatStudentAssistant(content),
    onError: () => {
      setChatMessages(prev => [...prev, {
        id: `err-${Date.now()}`,
        sender_type: 'assistant',
        message_body: "Sorry, I had a brief hiccup. Could you try that again?",
        sent_at: new Date().toISOString(),
      }])
    },
  })

  useEffect(() => {
    if (sendMut.data?.reply) {
      setChatMessages(prev => [...prev, {
        id: `assistant-${Date.now()}`,
        sender_type: 'assistant',
        message_body: sendMut.data!.reply,
        sent_at: new Date().toISOString(),
      }])
    }
  }, [sendMut.data])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [chatMessages])

  const handleSend = () => {
    const trimmed = input.trim()
    if (!trimmed || sendMut.isPending) return
    setChatMessages(prev => [...prev, {
      id: `student-${Date.now()}`,
      sender_type: 'student',
      message_body: trimmed,
      sent_at: new Date().toISOString(),
    }])
    sendMut.mutate(trimmed)
    setInput('')
  }

  const handleQuickAction = (action: string | (() => void)) => {
    if (typeof action === 'function') { action(); return }
    setInput(action)
  }

  // --- Welcome message ---
  const welcomeMsg = nextStep?.guidance_text
    || (completionPct < 30
      ? `Hi${user?.email ? ' ' + user.email.split('@')[0] : ''}! I'm your private college counselor. I'm here to help you through every step — from building your profile to landing your acceptance. What would you like to start with?`
      : completionPct < 80
        ? "Your story is coming together nicely. Let's keep building — what would you like to work on?"
        : matchCount > 0
          ? `You have ${matchCount} matched programs! Ask me anything about them, or let's start preparing your applications.`
          : "Your profile is strong. Ready to find programs that fit your story?")

  return (
    <div className="flex h-full">
      {/* ===== LEFT: Conversation Area (60%) ===== */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Chat header */}
        <div className="px-6 pt-5 pb-3">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 rounded-full bg-gold-soft flex items-center justify-center">
              <Sparkles size={20} className="text-gold" />
            </div>
            <div>
              <h1 className="text-lg font-semibold text-student-ink">Your Counselor</h1>
              <p className="text-xs text-student-text">I know your story. Ask me anything.</p>
            </div>
          </div>

          {/* Quick actions */}
          {chatMessages.length === 0 && (
            <div className="flex flex-wrap gap-2 mb-2">
              {quickActions.map((qa, i) => (
                <button
                  key={i}
                  onClick={() => handleQuickAction(qa.action)}
                  className="px-3 py-1.5 text-xs font-medium rounded-full bg-student-mist text-student hover:bg-student-moss transition-colors"
                >
                  {qa.label}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-6 space-y-3">
          {chatMessages.length === 0 && (
            <div className="flex gap-3">
              <div className="w-8 h-8 rounded-full bg-gold-soft flex items-center justify-center flex-shrink-0 mt-0.5">
                <Sparkles size={14} className="text-gold" />
              </div>
              <div className="bg-white rounded-2xl rounded-tl-md px-4 py-3 shadow-sm border border-divider max-w-lg">
                <p className="text-sm text-student-ink leading-relaxed">{welcomeMsg}</p>
              </div>
            </div>
          )}

          {chatMessages.map(msg => (
            <div key={msg.id} className={`flex gap-3 ${msg.sender_type === 'student' ? 'justify-end' : ''}`}>
              {msg.sender_type === 'assistant' && (
                <div className="w-8 h-8 rounded-full bg-gold-soft flex items-center justify-center flex-shrink-0 mt-0.5">
                  <Sparkles size={14} className="text-gold" />
                </div>
              )}
              <div className={`max-w-lg px-4 py-3 rounded-2xl text-sm leading-relaxed ${
                msg.sender_type === 'student'
                  ? 'bg-student text-white rounded-br-md'
                  : 'bg-white shadow-sm border border-divider text-student-ink rounded-bl-md'
              }`}>
                {msg.message_body}
              </div>
              {msg.sender_type === 'student' && (
                <Avatar name={user?.email || '?'} size="sm" />
              )}
            </div>
          ))}

          {sendMut.isPending && (
            <div className="flex gap-3">
              <div className="w-8 h-8 rounded-full bg-gold-soft flex items-center justify-center flex-shrink-0">
                <Sparkles size={14} className="text-gold" />
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
          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className="px-6 py-4 border-t border-divider bg-white">
          <div className="flex items-center gap-2">
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

      {/* ===== RIGHT: Context Panel (40%) ===== */}
      <aside className="w-80 xl:w-96 flex-shrink-0 border-l border-divider bg-white overflow-y-auto hidden lg:block">
        <div className="p-5 space-y-5">

          {/* Profile strength */}
          <div
            onClick={() => navigate('/s/profile')}
            className="flex items-center gap-3 p-3 rounded-xl bg-student-mist hover:bg-student-moss cursor-pointer transition-colors"
          >
            <div className="relative w-11 h-11 flex-shrink-0">
              <svg className="w-11 h-11 -rotate-90" viewBox="0 0 36 36">
                <circle cx="18" cy="18" r="15" fill="none" stroke="#D9E1DC" strokeWidth="2.5" />
                <circle cx="18" cy="18" r="15" fill="none" stroke="#2F5D50" strokeWidth="2.5"
                  strokeDasharray={`${completionPct * 0.94} 94`} strokeLinecap="round" />
              </svg>
              <span className="absolute inset-0 flex items-center justify-center text-[10px] font-bold text-student-ink">{completionPct}%</span>
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-xs font-semibold text-student-ink">My Story</p>
              <p className="text-[10px] text-student-text">
                {completionPct < 80 ? 'Keep building to unlock matches' : 'Profile is match-ready'}
              </p>
            </div>
            <ChevronRight size={14} className="text-student-text" />
          </div>

          {/* Active Applications */}
          <section>
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-xs font-semibold text-student-ink uppercase tracking-wider">Applications</h3>
              <span className="text-[10px] text-student-text">{activeApps.length} active</span>
            </div>
            {activeApps.length === 0 ? (
              <p className="text-xs text-student-text py-2">No applications yet. Ask me to help you get started.</p>
            ) : (
              <div className="space-y-2">
                {activeApps.slice(0, 4).map(app => {
                  const deadline = app.program?.application_deadline
                  const daysLeft = deadline ? differenceInDays(parseISO(deadline), new Date()) : null
                  return (
                    <button
                      key={app.id}
                      onClick={() => navigate(`/s/applications/${app.id}`)}
                      className="w-full text-left p-2.5 rounded-lg border border-divider hover:bg-student-mist transition-colors"
                    >
                      <p className="text-xs font-medium text-student-ink truncate">
                        {app.program?.program_name || 'Program'}
                      </p>
                      <div className="flex items-center gap-2 mt-1">
                        <Badge variant={app.status === 'draft' ? 'warning' : app.status === 'submitted' ? 'info' : 'success'} size="sm">
                          {app.status.replace(/_/g, ' ')}
                        </Badge>
                        {daysLeft != null && daysLeft >= 0 && daysLeft <= 30 && (
                          <span className="text-[10px] text-student-text flex items-center gap-0.5">
                            <Clock size={9} /> {daysLeft}d left
                          </span>
                        )}
                      </div>
                    </button>
                  )
                })}
              </div>
            )}
          </section>

          {/* Upcoming Deadlines */}
          {upcomingDeadlines.length > 0 && (
            <section>
              <h3 className="text-xs font-semibold text-student-ink uppercase tracking-wider mb-2">Deadlines</h3>
              <div className="space-y-1.5">
                {upcomingDeadlines.map((d, i) => {
                  const daysLeft = differenceInDays(d.date, new Date())
                  return (
                    <div key={i} className="flex items-center gap-2 text-xs">
                      <Calendar size={12} className={daysLeft <= 3 ? 'text-red-500' : daysLeft <= 7 ? 'text-amber-500' : 'text-student-text'} />
                      <span className="flex-1 truncate text-student-ink">{d.label}</span>
                      <span className={`font-medium ${daysLeft <= 3 ? 'text-red-600' : daysLeft <= 7 ? 'text-amber-600' : 'text-student-text'}`}>
                        {daysLeft === 0 ? 'Today' : daysLeft === 1 ? 'Tomorrow' : `${daysLeft}d`}
                      </span>
                    </div>
                  )
                })}
              </div>
            </section>
          )}

          {/* Saved Programs */}
          <section>
            <button
              onClick={() => navigate('/s/explore?tab=saved')}
              className="w-full flex items-center justify-between p-3 rounded-xl border border-divider hover:bg-student-mist transition-colors"
            >
              <div className="flex items-center gap-2">
                <Bookmark size={14} className="text-student" />
                <span className="text-xs font-medium text-student-ink">Saved Programs</span>
              </div>
              <div className="flex items-center gap-1">
                <span className="text-sm font-bold text-student">{savedCount}</span>
                <ChevronRight size={12} className="text-student-text" />
              </div>
            </button>
          </section>

          {/* Matches */}
          {matchCount > 0 && (
            <section>
              <button
                onClick={() => navigate('/s/explore')}
                className="w-full flex items-center justify-between p-3 rounded-xl border border-divider hover:bg-student-mist transition-colors"
              >
                <div className="flex items-center gap-2">
                  <GraduationCap size={14} className="text-gold" />
                  <span className="text-xs font-medium text-student-ink">AI Matches</span>
                </div>
                <div className="flex items-center gap-1">
                  <span className="text-sm font-bold text-gold">{matchCount}</span>
                  <ChevronRight size={12} className="text-student-text" />
                </div>
              </button>
            </section>
          )}

          {/* Explore CTA */}
          <button
            onClick={() => navigate('/s/explore')}
            className="w-full p-3 rounded-xl bg-student-mist hover:bg-student-moss transition-colors text-left"
          >
            <div className="flex items-center gap-2 mb-1">
              <Search size={14} className="text-student" />
              <span className="text-xs font-semibold text-student-ink">Explore Programs</span>
            </div>
            <p className="text-[10px] text-student-text">Browse schools, events, and community updates</p>
          </button>

        </div>
      </aside>
    </div>
  )
}

