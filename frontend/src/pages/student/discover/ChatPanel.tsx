/**
 * Discover → Chat panel.
 *
 * Owns the conversation for a single session. The session is created lazily
 * on the student's first message: no "start session" button required.
 *
 * Plan 2's LLM is the producer of `assistant`-role messages. When the
 * backend's `AI_DISCOVERY_V2_ENABLED` flag is on, replies come from the
 * real orchestrator; when off, the response is the Phase-A stub (clearly
 * marked with `_phase: 'A_stub'` so we render it visually distinct).
 */
import { useEffect, useRef, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import clsx from 'clsx'
import { ArrowUp, Sparkles } from 'lucide-react'

import {
  appendMessage,
  getSession,
  startSession,
} from '../../../api/discovery'
import Avatar from '../../../components/ui/Avatar'
import Button from '../../../components/ui/Button'
import { useAuthStore } from '../../../stores/auth-store'
import { showToast } from '../../../stores/toast-store'
import type {
  DiscoveryLayer,
  DiscoveryMessage,
  DiscoverySession,
  DiscoverySessionDetail,
  DiscoveryTrack,
} from '../../../types'

const PROMPTS_BY_TRACK: Record<DiscoveryTrack, string[]> = {
  profile: [
    'Tell me about a moment that shaped how you think.',
    'What do friends rely on you for?',
    "What's a belief about education you've revised in the last year?",
  ],
  goals: [
    'What does success look like a year after graduation?',
    "What's the one outcome that would make this whole journey worth it?",
    "What's a goal you've been afraid to name out loud?",
  ],
  needs: [
    "What can't you do without — housing, finance, healthcare?",
    'What kind of community do you need around you to thrive?',
    'What makes a school environment feel safe for you?',
  ],
}

export interface ChatPanelProps {
  track: DiscoveryTrack
  layer?: DiscoveryLayer
  /** Most-recent active session for the current track, if any. */
  session: DiscoverySession | null
  /** Called after a message round-trips so the parent can refresh
   *  completion / artifact widgets. */
  onTurnComplete?: () => void
}

function MessageBubble({ message }: { message: DiscoveryMessage }) {
  const isStudent = message.role === 'student'
  const isStub =
    message.role === 'assistant' &&
    message.extracted_signals != null &&
    typeof message.extracted_signals === 'object' &&
    (message.extracted_signals as Record<string, unknown>)._phase === 'A_stub'

  return (
    <div className={clsx('flex gap-2', isStudent ? 'justify-end' : 'justify-start')}>
      {!isStudent && (
        <div className="shrink-0 mt-0.5">
          <div className="h-7 w-7 rounded-full bg-student/10 flex items-center justify-center">
            <Sparkles size={14} className="text-student" />
          </div>
        </div>
      )}
      <div
        className={clsx(
          'rounded-2xl px-3.5 py-2 text-sm max-w-[80%] whitespace-pre-wrap break-words',
          isStudent
            ? 'bg-cobalt text-white rounded-br-sm'
            : isStub
              ? 'bg-amber-50 border border-amber-200 text-amber-900 rounded-bl-sm'
              : 'bg-student-bg-surface border border-divider text-student-ink rounded-bl-sm',
        )}
      >
        {message.content}
        {isStub && (
          <div className="text-[10px] uppercase tracking-wide text-amber-700 mt-1">
            stub — Plan 2 LLM not enabled
          </div>
        )}
      </div>
    </div>
  )
}

export default function ChatPanel({ track, layer, session, onTurnComplete }: ChatPanelProps) {
  const qc = useQueryClient()
  const user = useAuthStore(s => s.user)
  const [input, setInput] = useState('')
  const scrollRef = useRef<HTMLDivElement | null>(null)

  // Load full session w/ messages.
  const { data: detail } = useQuery<DiscoverySessionDetail | null>({
    queryKey: ['discovery', 'session', session?.id],
    queryFn: () => (session ? getSession(session.id) : Promise.resolve(null)),
    enabled: !!session,
  })

  // Auto-scroll to bottom on new messages.
  useEffect(() => {
    const el = scrollRef.current
    if (el) el.scrollTop = el.scrollHeight
  }, [detail?.messages.length])

  const turnMut = useMutation({
    mutationFn: async (content: string) => {
      // Lazily create a session on the first message.
      let sid = session?.id
      if (!sid) {
        const created = await startSession(track, track === 'profile' ? layer : undefined)
        sid = created.id
        // Tell react-query about the new session list.
        qc.invalidateQueries({ queryKey: ['discovery', 'sessions', track] })
      }
      return appendMessage(sid, { role: 'student', content })
    },
    onSuccess: () => {
      setInput('')
      qc.invalidateQueries({ queryKey: ['discovery', 'session', session?.id] })
      qc.invalidateQueries({ queryKey: ['discovery', 'completion'] })
      // Discovery-extracted artifacts may have been written; refresh the rail.
      qc.invalidateQueries({ queryKey: ['goals'] })
      qc.invalidateQueries({ queryKey: ['needs'] })
      qc.invalidateQueries({ queryKey: ['identity'] })
      onTurnComplete?.()
    },
    onError: (err: unknown) =>
      showToast((err as Error).message ?? 'Could not send message.', 'error'),
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const content = input.trim()
    if (!content) return
    turnMut.mutate(content)
  }

  const messages = detail?.messages ?? []
  const isEmpty = messages.length === 0

  return (
    <div className="flex flex-col h-full min-h-[500px]">
      {/* Messages */}
      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto space-y-3 pr-1 pb-3"
        aria-live="polite"
        aria-label="Discovery conversation"
      >
        {isEmpty ? (
          <EmptyState
            track={track}
            onPick={prompt => setInput(prompt)}
            firstName={user?.email?.split('@')[0]}
          />
        ) : (
          messages.map(m => <MessageBubble key={m.id} message={m} />)
        )}
        {turnMut.isPending && (
          <div className="flex justify-start">
            <div className="rounded-2xl px-3.5 py-2 text-sm bg-student-bg-surface border border-divider text-student-text rounded-bl-sm">
              <span className="inline-flex gap-1">
                <span className="h-1.5 w-1.5 rounded-full bg-student-text animate-pulse" />
                <span
                  className="h-1.5 w-1.5 rounded-full bg-student-text animate-pulse"
                  style={{ animationDelay: '150ms' }}
                />
                <span
                  className="h-1.5 w-1.5 rounded-full bg-student-text animate-pulse"
                  style={{ animationDelay: '300ms' }}
                />
              </span>
            </div>
          </div>
        )}
      </div>

      {/* Composer */}
      <form
        onSubmit={handleSubmit}
        className="flex items-end gap-2 border-t border-divider pt-3"
      >
        <textarea
          rows={2}
          maxLength={20000}
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault()
              handleSubmit(e)
            }
          }}
          placeholder={`Tell me about your ${track === 'profile' ? 'life' : track}…`}
          className="flex-1 resize-none rounded-lg border border-divider px-3 py-2 text-sm focus:outline-none focus:border-student"
          disabled={turnMut.isPending}
        />
        <Button
          type="submit"
          size="sm"
          loading={turnMut.isPending}
          disabled={!input.trim()}
          aria-label="Send message"
        >
          <ArrowUp size={16} />
        </Button>
      </form>
    </div>
  )
}

function EmptyState({
  track,
  onPick,
  firstName,
}: {
  track: DiscoveryTrack
  onPick: (prompt: string) => void
  firstName?: string
}) {
  const prompts = PROMPTS_BY_TRACK[track]
  return (
    <div className="py-8 space-y-4">
      <div className="flex items-center gap-3">
        <Avatar name={firstName ?? 'You'} size="md" />
        <div>
          <div className="text-sm font-medium text-student-ink">
            Let's explore your {track === 'profile' ? 'self' : track}.
          </div>
          <div className="text-xs text-student-text">
            Type freely. I'll listen, ask follow-ups, and build out your profile as we go.
          </div>
        </div>
      </div>
      <div className="grid gap-1.5">
        {prompts.map(p => (
          <button
            key={p}
            onClick={() => onPick(p)}
            className="text-left rounded-md border border-divider px-3 py-2 text-sm text-student-ink hover:border-student transition-colors"
          >
            {p}
          </button>
        ))}
      </div>
    </div>
  )
}
