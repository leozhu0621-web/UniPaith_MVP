import { useState, useEffect, useRef } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useAuthStore } from '../../stores/auth-store'
import {
  sendConversationTurn,
  getConversationSession,
  getConversationRequirements,
  getConversationConfidence,
  getShortlistUnlock,
  generateShortlist,
} from '../../api/matching'
import type {
  ConversationTurnResponse,
  ConversationRequirement,
  ConversationStage,
  ShortlistUnlock,
} from '../../types'
import Card from '../../components/ui/Card'
import Badge from '../../components/ui/Badge'
import Button from '../../components/ui/Button'
import Avatar from '../../components/ui/Avatar'
import Skeleton from '../../components/ui/Skeleton'
import { formatRelative } from '../../utils/format'
import { Sparkles, ArrowUp, Target, GraduationCap, ShieldCheck, ChevronRight } from 'lucide-react'

type ChatMessage = {
  id: string
  sender_type: 'student' | 'assistant'
  message_body: string
  sent_at: string
  suggested_next_actions?: string[]
}

const STAGES: { key: ConversationStage; label: string }[] = [
  { key: 'understand_context', label: 'Getting to know you' },
  { key: 'identify_issues', label: 'Understanding your needs' },
  { key: 'define_demand', label: 'Defining priorities' },
  { key: 'translate_requirements', label: 'Finalizing preferences' },
  { key: 'ready_for_shortlist', label: 'Ready for matches' },
]

function StageIndicator({ currentStage }: { currentStage: string }) {
  const currentIndex = STAGES.findIndex(s => s.key === currentStage)
  const activeIndex = currentIndex >= 0 ? currentIndex : 0

  return (
    <div className="flex items-center gap-1 px-4 py-2 overflow-x-auto">
      {STAGES.map((stage, i) => {
        const isActive = i === activeIndex
        const isComplete = i < activeIndex
        return (
          <div key={stage.key} className="flex items-center gap-1 flex-shrink-0">
            {i > 0 && (
              <ChevronRight
                size={12}
                className={isComplete || isActive ? 'text-stone-400' : 'text-gray-300'}
              />
            )}
            <span
              className={`text-xs px-2 py-0.5 rounded-full whitespace-nowrap ${
                isActive
                  ? 'bg-stone-600 text-white font-medium'
                  : isComplete
                    ? 'bg-emerald-100 text-emerald-700 font-medium'
                    : 'bg-gray-100 text-gray-400'
              }`}
            >
              {stage.label}
            </span>
          </div>
        )
      })}
    </div>
  )
}

function ConfidenceRing({ value }: { value: number }) {
  const radius = 44
  const stroke = 6
  const circumference = 2 * Math.PI * radius
  const offset = circumference - (value / 100) * circumference
  const color = value >= 75 ? '#059669' : value >= 50 ? '#E5A100' : '#57534e'

  return (
    <div className="relative w-28 h-28 flex-shrink-0 mx-auto">
      <svg className="w-28 h-28 -rotate-90" viewBox="0 0 100 100">
        <circle cx="50" cy="50" r={radius} fill="none" stroke="#e5e7eb" strokeWidth={stroke} />
        <circle
          cx="50"
          cy="50"
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth={stroke}
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          className="transition-all duration-700"
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-2xl font-bold text-stone-700">{Math.round(value)}%</span>
        <span className="text-[10px] text-gray-500">Confidence</span>
      </div>
    </div>
  )
}

const CONFIDENCE_LABELS: Record<string, { label: string; variant: 'neutral' | 'warning' | 'info' | 'success' }> = {
  insufficient: { label: 'Tell me more', variant: 'neutral' },
  provisional: { label: 'Getting clearer', variant: 'warning' },
  recommendation_ready: { label: 'Ready for matches', variant: 'info' },
  high_confidence: { label: 'Strong understanding', variant: 'success' },
}

function RequirementsList({ requirements }: { requirements: ConversationRequirement[] }) {
  const grouped = requirements.reduce<Record<string, ConversationRequirement[]>>((acc, req) => {
    const domain = req.domain || 'General'
    if (!acc[domain]) acc[domain] = []
    acc[domain].push(req)
    return acc
  }, {})

  const priorityVariant = (p: string): 'danger' | 'warning' | 'neutral' => {
    if (p === 'must_have') return 'danger'
    if (p === 'should_have') return 'warning'
    return 'neutral'
  }

  return (
    <div className="space-y-3">
      {Object.entries(grouped).map(([domain, reqs]) => (
        <div key={domain}>
          <p className="text-[10px] font-semibold uppercase tracking-wider text-gray-400 mb-1">
            {domain.replace(/_/g, ' ')}
          </p>
          <div className="space-y-1.5">
            {reqs.map(req => (
              <div key={req.requirement_id} className="flex items-center justify-between gap-2 text-sm">
                <div className="min-w-0">
                  <span className="text-stone-700 font-medium">{req.field}: </span>
                  <span className="text-gray-600">{String(req.value ?? '')}</span>
                </div>
                <Badge variant={priorityVariant(req.priority)} size="sm">
                  {req.priority === 'must_have' ? 'Must' : req.priority === 'should_have' ? 'Should' : 'Optional'}
                </Badge>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  )
}

interface ShortlistProgram {
  program_id: string
  program_name?: string
  institution_name?: string
  match_score?: number
  reasoning?: string
  category?: string
}

interface ShortlistData {
  eligible: boolean
  best_fit: ShortlistProgram[]
  stretch: ShortlistProgram[]
  safer: ShortlistProgram[]
  total: number
}

function ShortlistResults({ result }: { result: ShortlistData }) {
  const tiers: { key: 'best_fit' | 'stretch' | 'safer'; label: string; color: string }[] = [
    { key: 'best_fit', label: 'Best Fit', color: 'text-emerald-700' },
    { key: 'stretch', label: 'Stretch', color: 'text-amber-700' },
    { key: 'safer', label: 'Safer', color: 'text-sky-700' },
  ]

  return (
    <div className="space-y-4">
      {tiers.map(tier => {
        const programs = result[tier.key]
        if (!programs || programs.length === 0) return null
        return (
          <div key={tier.key}>
            <p className={`text-xs font-semibold uppercase tracking-wider mb-2 ${tier.color}`}>
              {tier.label}
            </p>
            <div className="space-y-2">
              {programs.map(prog => (
                <Card key={prog.program_id} className="p-3">
                  <div className="flex items-start justify-between gap-2">
                    <div className="min-w-0">
                      <p className="text-sm font-semibold text-stone-700 truncate">
                        {prog.program_name || prog.program_id}
                      </p>
                      {prog.institution_name && (
                        <p className="text-xs text-gray-500">{prog.institution_name}</p>
                      )}
                      {prog.reasoning && (
                        <p className="text-xs text-gray-500 mt-1 line-clamp-2">{prog.reasoning}</p>
                      )}
                    </div>
                    {prog.match_score != null && (
                      <div className="flex-shrink-0 text-right">
                        <span className="text-lg font-bold text-stone-700">
                          {Math.round(prog.match_score)}%
                        </span>
                      </div>
                    )}
                  </div>
                </Card>
              ))}
            </div>
          </div>
        )
      })}
    </div>
  )
}

export default function ProgramMatchPage() {
  const user = useAuthStore(s => s.user)
  const queryClient = useQueryClient()
  const [input, setInput] = useState('')
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([])
  const [sendError, setSendError] = useState<string | null>(null)
  const [shortlistResult, setShortlistResult] = useState<ShortlistData | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const { data: session } = useQuery({
    queryKey: ['match-session'],
    queryFn: getConversationSession,
    retry: false,
  })

  const { data: requirementsData } = useQuery({
    queryKey: ['match-requirements'],
    queryFn: getConversationRequirements,
    retry: false,
  })

  const { data: confidence } = useQuery({
    queryKey: ['match-confidence'],
    queryFn: getConversationConfidence,
    retry: false,
  })

  const { data: unlock } = useQuery({
    queryKey: ['match-unlock'],
    queryFn: getShortlistUnlock,
    retry: false,
  })

  const currentStage = session?.current_stage ?? 'understand_context'
  const globalConfidence = confidence?.global_confidence ?? 0
  const confidenceLevel: string = confidence?.global_level ?? 'insufficient'
  const missingDomains = (confidence?.domain_scores ?? [])
    .filter((d: any) => d.status === 'unknown' || d.status === 'partial')
    .map((d: any) => d.domain.replace(/_/g, ' '))
  const unlockData: ShortlistUnlock = unlock ?? { eligible: false, reasons: [], blocking_conflicts: [], missing_required_fields: [], recommended_next_actions: [] }
  const requirementsList: ConversationRequirement[] = requirementsData?.requirements ?? []
  const confidenceMeta = CONFIDENCE_LABELS[confidenceLevel] ?? CONFIDENCE_LABELS.insufficient

  const turnMut = useMutation({
    mutationFn: (message: string) =>
      sendConversationTurn(message, { session_id: session?.session_id }),
    onSuccess: (data: ConversationTurnResponse) => {
      const assistantMsg: ChatMessage = {
        id: `assistant-${Date.now()}`,
        sender_type: 'assistant',
        message_body: data.assistant_message.reply_text,
        sent_at: new Date().toISOString(),
        suggested_next_actions: data.assistant_message.suggested_next_actions,
      }
      setChatMessages(prev => [...prev, assistantMsg])
      setSendError(null)
      setInput('')
      queryClient.invalidateQueries({ queryKey: ['match-session'] })
      queryClient.invalidateQueries({ queryKey: ['match-requirements'] })
      queryClient.invalidateQueries({ queryKey: ['match-confidence'] })
      queryClient.invalidateQueries({ queryKey: ['match-unlock'] })
    },
    onError: (err) => {
      setSendError(err instanceof Error ? err.message : 'Message failed to send. Please try again.')
    },
  })

  const shortlistMut = useMutation({
    mutationFn: generateShortlist,
    onSuccess: (data: ShortlistData) => {
      setShortlistResult(data)
    },
  })

  const handleSend = () => {
    const trimmed = input.trim()
    if (!trimmed || turnMut.isPending) return
    const studentMsg: ChatMessage = {
      id: `student-${Date.now()}`,
      sender_type: 'student',
      message_body: trimmed,
      sent_at: new Date().toISOString(),
    }
    setChatMessages(prev => [...prev, studentMsg])
    turnMut.mutate(trimmed)
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleQuickAction = (action: string) => {
    setInput(action)
  }

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [chatMessages])

  const latestActions =
    [...chatMessages].reverse().find((m: ChatMessage) => m.sender_type === 'assistant')?.suggested_next_actions ?? []

  const sidebar = (
    <div className="w-80 flex-shrink-0 border-l border-gray-100 bg-white overflow-y-auto hidden lg:block">
      <div className="p-4 space-y-5">
        <Card className="p-4 text-center">
          <ConfidenceRing value={globalConfidence} />
          <Badge variant={confidenceMeta.variant} className="mt-2">
            {confidenceMeta.label}
          </Badge>
          {missingDomains.length > 0 && (
            <p className="text-xs text-gray-500 mt-2">
              Still exploring: {missingDomains.join(', ')}
            </p>
          )}
        </Card>

        {requirementsList.length > 0 && (
          <Card className="p-4">
            <div className="flex items-center gap-2 mb-3">
              <Target size={14} className="text-stone-600" />
              <p className="text-xs font-semibold text-stone-700 uppercase tracking-wider">
                Your Requirements
              </p>
            </div>
            <RequirementsList requirements={requirementsList} />
          </Card>
        )}

        <Button
          onClick={() => shortlistMut.mutate()}
          disabled={!unlockData.eligible || shortlistMut.isPending}
          loading={shortlistMut.isPending}
          className="w-full"
          size="md"
        >
          <GraduationCap size={16} className="mr-2" />
          Generate Shortlist
        </Button>
        {!unlockData.eligible && unlockData.recommended_next_actions.length > 0 && (
          <p className="text-xs text-gray-500 text-center -mt-2">
            {unlockData.recommended_next_actions[0]}
          </p>
        )}

        {shortlistResult && (
          <div>
            <p className="text-xs font-semibold text-stone-700 uppercase tracking-wider mb-2">
              Your Shortlist
            </p>
            <ShortlistResults result={shortlistResult} />
          </div>
        )}
      </div>
    </div>
  )

  return (
    <div className="flex h-full">
      <div className="flex-1 flex flex-col min-w-0">
        <div className="px-4 py-2 border-b border-gray-100 bg-white">
          <div className="flex items-center gap-2 mb-1">
            <Sparkles size={16} className="text-amber-500" />
            <h1 className="text-lg font-semibold text-stone-700">Program Match</h1>
          </div>
          <StageIndicator currentStage={currentStage} />
        </div>

        <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4 bg-stone-50">
          {chatMessages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-center">
              <div className="w-16 h-16 rounded-full bg-amber-50 flex items-center justify-center mb-4">
                <Sparkles size={28} className="text-amber-500" />
              </div>
              <h2 className="text-lg font-medium text-stone-600">
                Let's find the right programs for you.
              </h2>
              <p className="text-sm text-gray-500 mt-1 max-w-md">
                Tell me about your goals, interests, and what matters most to you in a program.
                I will listen, learn, and match you with programs that truly fit.
              </p>
              <div className="mt-3 flex items-center gap-2 text-xs text-gray-500 bg-white rounded-full px-3 py-1 shadow-sm">
                <ShieldCheck size={13} className="text-gray-600" />
                Your answers build a personalized match profile.
              </div>
            </div>
          ) : (
            chatMessages.map(msg => {
              const isOwn = msg.sender_type === 'student'
              return (
                <div key={msg.id} className={`flex ${isOwn ? 'justify-end' : 'justify-start'}`}>
                  <div className={`flex gap-2 max-w-[80%] ${isOwn ? 'flex-row-reverse' : ''}`}>
                    <Avatar name={isOwn ? (user?.email || '?') : 'Match'} size="sm" />
                    <div>
                      <div
                        className={`px-4 py-2 rounded-2xl text-sm whitespace-pre-wrap ${
                          isOwn
                            ? 'bg-stone-700 text-white rounded-br-md'
                            : 'bg-white shadow-sm text-stone-700 rounded-bl-md'
                        }`}
                      >
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

          {turnMut.isPending && (
            <div className="flex justify-start">
              <div className="flex gap-2 max-w-[80%]">
                <Avatar name="Match" size="sm" />
                <div className="px-4 py-3 rounded-2xl rounded-bl-md bg-white shadow-sm">
                  <div className="flex gap-1">
                    <Skeleton className="w-2 h-2 rounded-full" />
                    <Skeleton className="w-2 h-2 rounded-full" />
                    <Skeleton className="w-2 h-2 rounded-full" />
                  </div>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        <div className="px-6 py-3 border-t border-gray-100 bg-white">
          <div className="flex items-end gap-2">
            <textarea
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Tell me about what you're looking for..."
              rows={1}
              className="flex-1 resize-none border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-stone-700"
            />
            <button
              onClick={handleSend}
              disabled={!input.trim() || turnMut.isPending}
              className="p-2 bg-stone-700 text-white rounded-lg hover:bg-stone-600 disabled:opacity-50"
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
            {latestActions.map((action: string, i: number) => (
              <button
                key={i}
                onClick={() => handleQuickAction(action)}
                className="px-3 py-1 text-xs bg-gray-100 text-gray-600 rounded-full hover:bg-gray-200 whitespace-nowrap flex-shrink-0"
              >
                {action}
              </button>
            ))}
          </div>

          <div className="lg:hidden mt-3 flex items-center justify-between gap-3">
            <div className="flex items-center gap-2">
              <span className="text-xs text-gray-500">
                Confidence: {Math.round(globalConfidence)}%
              </span>
              <Badge variant={confidenceMeta.variant} size="sm">
                {confidenceMeta.label}
              </Badge>
            </div>
            <Button
              onClick={() => shortlistMut.mutate()}
              disabled={!unlockData.eligible || shortlistMut.isPending}
              loading={shortlistMut.isPending}
              size="sm"
            >
              Generate Shortlist
            </Button>
          </div>
        </div>
      </div>

      {sidebar}
    </div>
  )
}
