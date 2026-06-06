/**
 * Discover redesign — the single-column conversation with Uni (a real college
 * counselor). No tracks, layers, progress %, or rails: just the conversation.
 * One unified session feeds goals/needs/identity behind the scenes.
 */
import { Fragment, useEffect, useMemo, useRef, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import clsx from 'clsx'
import { ArrowUp } from 'lucide-react'

import {
  appendMessage,
  getSession,
  listSessions,
  startUnifiedSession,
} from '../../../api/discovery'
import { getLivingProfile } from '../../../api/livingProfile'
import type { LivingProfile } from '../../../api/livingProfile'
import Button from '../../../components/ui/Button'
import { useAuthStore } from '../../../stores/auth-store'
import { showToast } from '../../../stores/toast-store'
import type {
  AppendMessageResponse,
  DiscoveryMessage,
  DiscoverySession,
  DiscoverySessionDetail,
} from '../../../types'
import MatchHandoffCard from './MatchHandoffCard'
import NoticedCard from './NoticedCard'
import { attachRefs, noticedItemsFromSignals } from './noticed'
import ProfileDrawer from './ProfileDrawer'

// Counselor-style ways-in for a stuck student — gentle fallbacks, not the
// primary interaction (Uni leads the conversation).
const QUICK_REPLIES = [
  "I'm not sure where to start",
  'Could you give an example?',
  'You ask me',
] as const

function UniBubble({ message }: { message: DiscoveryMessage }) {
  const isStudent = message.role === 'student'
  return (
    <div className={clsx('flex gap-2.5', isStudent ? 'justify-end' : 'justify-start')}>
      {!isStudent && (
        <div className="h-7 w-7 rounded-full bg-secondary text-white flex items-center justify-center shrink-0 mt-0.5 text-xs font-semibold">
          U
        </div>
      )}
      <div
        className={clsx(
          'rounded-2xl px-3.5 py-2 text-sm whitespace-pre-wrap break-words max-w-[80%] leading-relaxed',
          isStudent
            ? 'bg-secondary text-white rounded-br-sm'
            : 'bg-card border border-border text-foreground rounded-bl-sm',
        )}
      >
        {message.content}
      </div>
    </div>
  )
}

export default function UniConversation({
  profileOpen = false,
  onProfileOpenChange,
}: {
  /** Living-profile drawer open state (the trigger lives in DiscoverHomePage). */
  profileOpen?: boolean
  onProfileOpenChange?: (open: boolean) => void
} = {}) {
  const qc = useQueryClient()
  const user = useAuthStore(s => s.user)
  const firstName = user?.email?.split('@')[0]
  const scrollRef = useRef<HTMLDivElement | null>(null)
  const [draft, setDraft] = useState('')
  const [sessionId, setSessionId] = useState<string | null>(null)
  // The student can wave off Uni's handoff offer; it re-surfaces after the next
  // turn (reset in the mutation's onSuccess).
  const [handoffDismissed, setHandoffDismissed] = useState(false)

  // Resolve the active unified (discovery) session, if any.
  const { data: sessions = [], isPending: sessionsLoading } = useQuery<DiscoverySession[]>({
    queryKey: ['discovery', 'sessions', 'unified'],
    queryFn: () => listSessions({ status: 'active' }),
  })
  const resolvedSessionId = useMemo(
    () =>
      sessions
        .filter(s => (s.track as string) === 'discovery')
        .sort((a, b) => b.started_at.localeCompare(a.started_at))[0]?.id ?? null,
    [sessions],
  )
  useEffect(() => {
    if (sessionId) return
    if (resolvedSessionId) setSessionId(resolvedSessionId)
  }, [resolvedSessionId, sessionId])

  const { data: detail } = useQuery<DiscoverySessionDetail | null>({
    queryKey: ['discovery', 'session', sessionId],
    queryFn: () => (sessionId ? getSession(sessionId) : Promise.resolve(null)),
    enabled: !!sessionId,
  })
  const messages = useMemo(() => detail?.messages ?? [], [detail?.messages])
  const isEmpty = messages.length === 0

  // The living profile gives the in-thread "Noticed" chips their editable refs
  // (label → saved goal/need id) and backs the drawer.
  const { data: livingProfile } = useQuery<LivingProfile>({
    queryKey: ['discovery', 'livingProfile'],
    queryFn: getLivingProfile,
    enabled: !isEmpty,
  })

  const turnMut = useMutation({
    mutationFn: async (content: string) => {
      // Reuse the session already loaded from listSessions before creating a new
      // one — relying solely on `sessionId` state can race the effect that binds
      // it, splitting the conversation across two sessions.
      let sid = sessionId ?? resolvedSessionId
      if (!sid) {
        const created = await startUnifiedSession()
        sid = created.id
        qc.invalidateQueries({ queryKey: ['discovery', 'sessions', 'unified'] })
      }
      if (sid !== sessionId) setSessionId(sid)
      return appendMessage(sid, { role: 'student', content })
    },
    onSuccess: (data: AppendMessageResponse) => {
      setDraft('')
      setHandoffDismissed(false)
      const sid = data.student_message.session_id
      qc.invalidateQueries({ queryKey: ['discovery', 'session', sid] })
      qc.invalidateQueries({ queryKey: ['discovery', 'completion'] })
      qc.invalidateQueries({ queryKey: ['discovery', 'handoff'] })
      qc.invalidateQueries({ queryKey: ['discovery', 'livingProfile'] })
      qc.invalidateQueries({ queryKey: ['goals'] })
      qc.invalidateQueries({ queryKey: ['needs'] })
      qc.invalidateQueries({ queryKey: ['identity'] })
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
    // Wait for the sessions query to settle so we don't spawn a duplicate
    // session while an existing one is still loading.
    if (!text || turnMut.isPending || sessionsLoading) return
    turnMut.mutate(text)
  }

  return (
    <div className="flex flex-col h-full min-h-[520px] max-w-[640px] mx-auto w-full">
      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto space-y-3.5 pr-1 pb-3"
        aria-live="polite"
        aria-label="Conversation with Uni"
      >
        {isEmpty ? (
          <div className="flex gap-2.5 py-6">
            <div className="h-7 w-7 rounded-full bg-secondary text-white flex items-center justify-center shrink-0 mt-0.5 text-xs font-semibold">
              U
            </div>
            <div className="bg-card border border-border rounded-2xl rounded-bl-sm px-3.5 py-2.5 text-sm leading-relaxed text-foreground max-w-[80%]">
              {firstName ? `Hi ${firstName} — ` : 'Hi — '}I'm Uni, your counselor for this. My
              job is to help you find where you'll genuinely thrive, not just where you can get
              in. There are no wrong answers here; we're just getting to know you.
              <br />
              <br />
              To start simple: thinking back over this past year, when was a moment — in class or
              outside it — that you felt really absorbed?
            </div>
          </div>
        ) : (
          messages.map(m => {
            const noticed = attachRefs(
              noticedItemsFromSignals(m.extracted_signals),
              livingProfile,
            )
            return (
              <Fragment key={m.id}>
                <UniBubble message={m} />
                {noticed.length > 0 && (
                  <NoticedCard items={noticed} onAdjust={() => onProfileOpenChange?.(true)} />
                )}
              </Fragment>
            )
          })
        )}
        {turnMut.isPending && (
          <div className="flex justify-start gap-2.5">
            <div className="h-7 w-7 rounded-full bg-secondary text-white flex items-center justify-center shrink-0 text-xs font-semibold">
              U
            </div>
            <div className="rounded-2xl px-3.5 py-2 bg-card border border-border rounded-bl-sm">
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

        {!isEmpty && !handoffDismissed && (
          <MatchHandoffCard variant="auto" onKeepTalking={() => setHandoffDismissed(true)} />
        )}
      </div>

      {!turnMut.isPending && (
        <div className="mb-2 flex flex-wrap gap-1.5">
          {QUICK_REPLIES.map(s => (
            <button
              key={s}
              type="button"
              onClick={() => send(s)}
              className="text-xs px-2.5 py-1 rounded-full border border-border text-muted-foreground hover:border-foreground/30 transition-colors"
            >
              {s}
            </button>
          ))}
        </div>
      )}

      <form
        onSubmit={e => {
          e.preventDefault()
          send(draft)
        }}
        className="flex items-end gap-2 border-t border-border pt-3"
      >
        <textarea
          rows={2}
          maxLength={20000}
          value={draft}
          onChange={e => setDraft(e.target.value)}
          onKeyDown={e => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault()
              send(draft)
            }
          }}
          placeholder="Tell Uni what's on your mind…"
          className="flex-1 resize-none rounded-lg border border-border bg-background px-3 py-2 text-sm focus:outline-none focus:border-secondary"
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

      <ProfileDrawer
        isOpen={profileOpen}
        onClose={() => onProfileOpenChange?.(false)}
        onAsk={prompt => {
          onProfileOpenChange?.(false)
          send(prompt)
        }}
      />
    </div>
  )
}
