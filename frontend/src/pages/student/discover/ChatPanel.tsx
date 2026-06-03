/**
 * Discover → Chat panel (spec 19 §3–§5, §9).
 */
import { useEffect, useMemo, useRef, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import clsx from 'clsx'
import { ArrowUp, Info, Sparkles } from 'lucide-react'

import { appendMessage, getSession, startSession } from '../../../api/discovery'
import Avatar from '../../../components/ui/Avatar'
import Button from '../../../components/ui/Button'
import { useAuthStore } from '../../../stores/auth-store'
import { showToast } from '../../../stores/toast-store'
import type {
  AppendMessageResponse,
  AssistantTurnSignals,
  DiscoveryLayer,
  DiscoveryMessage,
  DiscoverySession,
  DiscoverySessionDetail,
  DiscoveryTrack,
} from '../../../types'
import { PROFILE_BASIC_CHIP_PROMPTS } from './discoveryConstants'

const PROMPTS_BY_TRACK: Record<DiscoveryTrack, string[]> = {
  profile: ['Tell me about a course you actually enjoyed this year.'],
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

const ALWAYS_REPLIES = ['I don’t know yet', 'Skip this'] as const
const TRACK_ORDER: DiscoveryTrack[] = ['profile', 'goals', 'needs']

export interface ChatPanelProps {
  track: DiscoveryTrack
  layer?: DiscoveryLayer
  session: DiscoverySession | null
  draft: string
  onDraftChange: (value: string) => void
  onTurnComplete?: () => void
  onSwitchTrack?: (t: DiscoveryTrack) => void
  onSessionCreated?: (sessionId: string) => void
}

function signalsOf(message: DiscoveryMessage): AssistantTurnSignals {
  const s = message.extracted_signals
  return (s && typeof s === 'object' ? s : {}) as AssistantTurnSignals
}

function MessageBubble({ message }: { message: DiscoveryMessage }) {
  const isStudent = message.role === 'student'
  return (
    <div className={clsx('flex gap-2', isStudent ? 'justify-end' : 'justify-start')}>
      {!isStudent && (
        <div className="shrink-0 mt-0.5">
          <div className="h-7 w-7 rounded-full bg-muted flex items-center justify-center">
            <Sparkles size={14} className="text-accent" />
          </div>
        </div>
      )}
      <div className={clsx('flex flex-col max-w-[80%]', isStudent ? 'items-end' : 'items-start')}>
        {!isStudent && (
          <span className="text-[10px] uppercase tracking-wide text-muted-foreground mb-0.5 px-1">
            Counselor
          </span>
        )}
        <div
          className={clsx(
            'rounded-2xl px-3.5 py-2 text-sm whitespace-pre-wrap break-words',
            isStudent
              ? 'bg-muted text-foreground rounded-br-sm'
              : 'bg-card border border-border text-foreground rounded-bl-sm',
          )}
        >
          {message.content}
        </div>
      </div>
    </div>
  )
}

export default function ChatPanel({
  track,
  layer,
  session,
  draft,
  onDraftChange,
  onTurnComplete,
  onSwitchTrack,
  onSessionCreated,
}: ChatPanelProps) {
  const qc = useQueryClient()
  const user = useAuthStore(s => s.user)
  const scrollRef = useRef<HTMLDivElement | null>(null)

  const [resolvedSessionId, setResolvedSessionId] = useState<string | null>(session?.id ?? null)
  useEffect(() => {
    setResolvedSessionId(session?.id ?? null)
  }, [session?.id])

  const { data: detail } = useQuery<DiscoverySessionDetail | null>({
    queryKey: ['discovery', 'session', resolvedSessionId],
    queryFn: () =>
      resolvedSessionId ? getSession(resolvedSessionId) : Promise.resolve(null),
    enabled: !!resolvedSessionId,
  })

  const messages = useMemo(() => detail?.messages ?? [], [detail?.messages])

  const turnMut = useMutation({
    mutationFn: async (content: string) => {
      let sid = resolvedSessionId
      if (!sid) {
        const created = await startSession(track, track === 'profile' ? layer : undefined)
        sid = created.id
        setResolvedSessionId(created.id)
        onSessionCreated?.(created.id)
        qc.invalidateQueries({ queryKey: ['discovery', 'sessions', track] })
      }
      return appendMessage(sid, { role: 'student', content })
    },
    onSuccess: (data: AppendMessageResponse) => {
      onDraftChange('')
      const sid = data.student_message.session_id
      qc.invalidateQueries({ queryKey: ['discovery', 'session', sid] })
      qc.invalidateQueries({ queryKey: ['discovery', 'sessions', track] })
      qc.invalidateQueries({ queryKey: ['discovery', 'completion'] })
      qc.invalidateQueries({ queryKey: ['goals'] })
      qc.invalidateQueries({ queryKey: ['needs'] })
      qc.invalidateQueries({ queryKey: ['identity'] })
      qc.invalidateQueries({ queryKey: ['personality-signals'] })
      onTurnComplete?.()
    },
    onError: (err: unknown) =>
      showToast((err as Error).message ?? 'Could not send message.', 'error'),
  })

  useEffect(() => {
    const el = scrollRef.current
    if (el) el.scrollTop = el.scrollHeight
  }, [messages.length, turnMut.isPending])

  const send = (content: string) => {
    const text = content.trim()
    if (!text || turnMut.isPending) return
    turnMut.mutate(text)
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    send(draft)
  }

  const handleSwitchTrack = () => {
    const idx = TRACK_ORDER.indexOf(track)
    onSwitchTrack?.(TRACK_ORDER[(idx + 1) % TRACK_ORDER.length])
  }

  const isEmpty = messages.length === 0
  const showBasicChips = track === 'profile' && (layer ?? 'basic') === 'basic'

  const lastAssistant = useMemo(
    () => [...messages].reverse().find(m => m.role === 'assistant'),
    [messages],
  )
  const lastSignals = lastAssistant ? signalsOf(lastAssistant) : {}
  const suggested = Array.isArray(lastSignals.suggested_options)
    ? lastSignals.suggested_options.filter(s => typeof s === 'string' && s.trim())
    : []
  const limitedMode = lastSignals._mode === 'rule_based' || lastSignals._phase === 'A2_error'
  const chipPrompts = showBasicChips && suggested.length === 0 ? [...PROFILE_BASIC_CHIP_PROMPTS] : suggested
  const showChipRow = !isEmpty && !turnMut.isPending && chipPrompts.length > 0

  return (
    <div className="flex flex-col h-full min-h-[500px]">
      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto space-y-3 pr-1 pb-3"
        aria-live="polite"
        aria-label="Discovery conversation"
      >
        {isEmpty ? (
          <EmptyState
            track={track}
            layer={layer}
            onPick={onDraftChange}
            onSend={send}
            firstName={user?.email?.split('@')[0]}
          />
        ) : (
          messages.map(m => <MessageBubble key={m.id} message={m} />)
        )}
        {turnMut.isPending && (
          <div className="flex justify-start gap-2">
            <div className="h-7 w-7 rounded-full bg-muted flex items-center justify-center shrink-0">
              <Sparkles size={14} className="text-accent" />
            </div>
            <div className="rounded-2xl px-3.5 py-2 text-sm bg-card border border-border text-muted-foreground rounded-bl-sm">
              <span className="inline-flex gap-1">
                <span className="h-1.5 w-1.5 rounded-full bg-muted-foreground animate-pulse" />
                <span
                  className="h-1.5 w-1.5 rounded-full bg-muted-foreground animate-pulse"
                  style={{ animationDelay: '150ms' }}
                />
                <span
                  className="h-1.5 w-1.5 rounded-full bg-muted-foreground animate-pulse"
                  style={{ animationDelay: '300ms' }}
                />
              </span>
            </div>
          </div>
        )}
      </div>

      {limitedMode && !turnMut.isPending && (
        <div className="mb-2 flex items-center gap-2 rounded-md border border-warning/40 bg-warning/10 px-3 py-1.5 text-xs text-foreground">
          <Info size={13} className="text-warning shrink-0" />
          Limited mode active — your replies are still saved.
        </div>
      )}

      {!isEmpty && !turnMut.isPending && (
        <div className="mb-2 space-y-1.5">
          {showChipRow && (
            <>
              <div className="text-[10px] uppercase tracking-wide text-muted-foreground">
                Suggested prompts
              </div>
              <div className="flex flex-wrap gap-1.5">
                {chipPrompts.map(s => (
                  <button
                    key={s}
                    type="button"
                    onClick={() => send(s)}
                    className="text-xs px-2.5 py-1 rounded-full border border-secondary/50 text-secondary hover:bg-secondary/5 transition-colors"
                  >
                    {s}
                  </button>
                ))}
              </div>
            </>
          )}
          <div className="flex flex-wrap gap-1.5">
            {ALWAYS_REPLIES.map(s => (
              <button
                key={s}
                type="button"
                onClick={() => send(s)}
                className="text-xs px-2.5 py-1 rounded-full border border-border text-muted-foreground hover:border-foreground/30 transition-colors"
              >
                {s}
              </button>
            ))}
            {onSwitchTrack && (
              <button
                type="button"
                onClick={handleSwitchTrack}
                className="text-xs px-2.5 py-1 rounded-full border border-border text-muted-foreground hover:border-foreground/30 transition-colors"
              >
                Switch track
              </button>
            )}
          </div>
        </div>
      )}

      <form onSubmit={handleSubmit} className="flex items-end gap-2 border-t border-border pt-3">
        <textarea
          rows={2}
          maxLength={20000}
          value={draft}
          onChange={e => onDraftChange(e.target.value)}
          onKeyDown={e => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault()
              handleSubmit(e)
            }
          }}
          placeholder={`Tell me about your ${track === 'profile' ? 'life' : track}…`}
          className="flex-1 resize-none rounded-lg border border-border bg-background px-3 py-2 text-sm focus:outline-none focus:border-accent"
          disabled={turnMut.isPending}
        />
        <Button
          type="submit"
          variant="secondary"
          size="sm"
          loading={turnMut.isPending}
          disabled={!draft.trim()}
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
  layer,
  onPick,
  onSend,
  firstName,
}: {
  track: DiscoveryTrack
  layer?: DiscoveryLayer
  onPick: (prompt: string) => void
  onSend: (prompt: string) => void
  firstName?: string
}) {
  const showBasicChips = track === 'profile' && (layer ?? 'basic') === 'basic'
  const prompts = PROMPTS_BY_TRACK[track]
  const chips = showBasicChips ? [...PROFILE_BASIC_CHIP_PROMPTS] : prompts

  return (
    <div className="py-8 space-y-4">
      <div className="flex items-center gap-3">
        <Avatar name={firstName ?? 'You'} size="md" />
        <div>
          <div className="text-sm font-medium text-foreground">
            {showBasicChips
              ? 'Tell me about a course you actually enjoyed this year.'
              : `Let's explore your ${track === 'profile' ? 'self' : track}.`}
          </div>
          <div className="text-xs text-muted-foreground">
            Type freely. I'll listen, ask follow-ups, and build out your profile as we go.
          </div>
        </div>
      </div>
      <div className="text-[10px] uppercase tracking-wide text-muted-foreground">Suggested prompts</div>
      <div className="grid gap-1.5">
        {chips.map(p => (
          <button
            key={p}
            type="button"
            onClick={() => (showBasicChips ? onSend(p) : onPick(p))}
            className="text-left rounded-md border border-secondary/40 px-3 py-2 text-sm text-foreground hover:border-secondary hover:bg-secondary/5 transition-colors"
          >
            {p}
          </button>
        ))}
      </div>
    </div>
  )
}
