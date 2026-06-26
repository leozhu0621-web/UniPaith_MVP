/**
 * Discover redesign — the single-column conversation with Uni (a real college
 * counselor). No tracks, layers, progress %, or rails: just the conversation.
 * One unified session feeds goals/needs/identity behind the scenes.
 */
import { Fragment, useEffect, useMemo, useRef, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { ArrowUp, Paperclip } from 'lucide-react'

import {
  appendMessage,
  getSession,
  listSessions,
  startUnifiedSession,
  streamDiscoveryMessage,
  streamDiscoveryOpener,
} from '../../../api/discovery'
import { getLivingProfile } from '../../../api/livingProfile'
import type { LivingProfile } from '../../../api/livingProfile'
import { updateSession as updateChatSession } from '../../../api/chatSessions'
import Button from '../../../components/ui/Button'
import { getProfile } from '../../../api/students'
import { showToast } from '../../../stores/toast-store'
import type {
  AppendMessageResponse,
  DiscoveryMessage,
  DiscoverySession,
  DiscoverySessionDetail,
} from '../../../types'
import MaterialUpload from '../../../components/student/MaterialUpload'
import EnrichWidget from '../../../components/student/EnrichWidget'
import AnswerChoices from './AnswerChoices'
import UniOrb, { type OrbState } from '../../../components/student/UniOrb'
import { deriveComposerOrbState } from './composerOrbState'
import FirstLookCard from './FirstLookCard'
import NoticedCard from './NoticedCard'
import { attachRefs, noticedItemsFromSignals } from './noticed'
import ProfileDrawer from './ProfileDrawer'
import { useJourneyState } from './useJourneyState'

/**
 * Inline enrich widget — a structured Prompt-Library card that appears in the
 * Uni thread after the most recent assistant message.  It lets the student fill
 * the next missing profile signal without leaving the chat. Renders nothing
 * when the profile is complete (getEnrichNext returns no items) or when Uni is
 * still streaming (avoids flickering in the middle of a reply).
 *
 * Sits in Uni's column (left-aligned, indented past the orb) to read as part
 * of the assistant's turn, matching the chat-with-widgets.html mockup.
 */
function InlineChatEnrichCard() {
  return (
    // Indent past the 28px orb + 10px gap so the card aligns with Uni's bubbles.
    <div className="pl-[38px]">
      <EnrichWidget inline />
    </div>
  )
}

function UniBubble({
  message,
  orbState = 'idle',
}: {
  message: DiscoveryMessage
  orbState?: OrbState
}) {
  const isStudent = message.role === 'student'

  // Student — a soft cobalt-tint bubble, right-aligned (never dark/black). (§5)
  if (isStudent) {
    return (
      <div className="flex justify-end">
        <div className="rounded-2xl rounded-br-sm bg-secondary/10 border border-secondary/15 px-3.5 py-2 text-sm whitespace-pre-wrap break-words max-w-[80%] leading-relaxed text-foreground">
          {message.content}
        </div>
      </div>
    )
  }

  // Advisor — the orb + the message as plain text (no bubble), counselor voice. (§5)
  return (
    <div className="flex gap-2.5 justify-start">
      <UniOrb state={orbState} className="mt-0.5" />
      <div className="pt-0.5 text-sm whitespace-pre-wrap break-words max-w-[80%] leading-relaxed text-foreground">
        {message.content}
      </div>
    </div>
  )
}

export default function UniConversation({
  profileOpen = false,
  onProfileOpenChange,
  guided = false,
  onReady,
  prefill,
  conversationSessionId = null,
  chatSessionId = null,
}: {
  /** Living-profile drawer open state (the trigger lives in DiscoverHomePage). */
  profileOpen?: boolean
  onProfileOpenChange?: (open: boolean) => void
  /** Guided shell: show the stage header + earned Continue. */
  guided?: boolean
  /** Register an imperative `ask` so the rail can drive the conversation. */
  onReady?: (api: { ask: (text: string) => void }) => void
  /** Cross-sell hand-off question (from /s?prefill=…) — sent as the opening turn. */
  prefill?: string
  /** Chat-tab resume: the discovery thread bound to the open chat session
   *  (null until its first turn). When set, this thread loads instead of the
   *  global most-recent one. The component should be keyed by chat session so a
   *  switch remounts with the right thread. */
  conversationSessionId?: string | null
  /** The open chat session's id. When set, the conversation is bound to it:
   *  it never grabs the global most-recent thread, and the first turn writes the
   *  new thread id back onto the chat session (so reload resumes it). */
  chatSessionId?: string | null
} = {}) {
  const qc = useQueryClient()
  // Greet by the student's real first name (todo 3.1) — NEVER the email local-part.
  // The shared ['profile'] cache is usually already warm (My Space / Profile); if
  // the name is unknown the greeting falls back to name-less ("Hi —"), not a handle.
  const { data: profile } = useQuery({
    queryKey: ['profile'],
    queryFn: getProfile,
    staleTime: 300_000,
  })
  const firstName = (profile?.first_name || profile?.preferred_name || '').trim()
  const scrollRef = useRef<HTMLDivElement | null>(null)
  const [draft, setDraft] = useState('')
  const [showUpload, setShowUpload] = useState(false)
  // When bound to a chat session, start on its thread (null for a fresh one).
  // ChatTabShell keys this component by chat session, so a switch remounts and
  // re-seeds from the right thread.
  const boundToChat = chatSessionId != null
  const [sessionId, setSessionId] = useState<string | null>(conversationSessionId)
  // The student can wave off Uni's handoff offer; it re-surfaces after the next
  // turn (reset in the mutation's onSuccess).
  const [handoffDismissed, setHandoffDismissed] = useState(false)

  // Token-streaming state (Spec 77 §6) — optimistic student bubble + an
  // accumulating assistant bubble while Uni streams; cleared once the canonical
  // session reloads. Falls back to the non-stream turnMut path on error.
  const streamAbort = useRef<AbortController | null>(null)
  const [streaming, setStreaming] = useState(false)
  const [streamStudent, setStreamStudent] = useState<DiscoveryMessage | null>(null)
  const [streamText, setStreamText] = useState('')
  // True when a streamed turn errored mid-flight (managed agent / platform
  // hiccup) — the backend can't always stamp the degraded marker on that path,
  // so we surface the "limited mode" banner locally too (todo 2.5).
  const [streamDegraded, setStreamDegraded] = useState(false)
  // Proactive opener (Uni speaks first): fired once when the conversation loads
  // empty. `openerFailed` falls back to the static greeting if it can't stream.
  const openerFired = useRef(false)
  const [openerFailed, setOpenerFailed] = useState(false)
  const canStream =
    typeof window !== 'undefined' &&
    typeof ReadableStream !== 'undefined' &&
    !window.matchMedia?.('(prefers-reduced-motion: reduce)').matches
  useEffect(() => () => streamAbort.current?.abort(), [])

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
    if (boundToChat) return // bound to a chat session — never grab the global thread
    if (sessionId) return
    if (resolvedSessionId) setSessionId(resolvedSessionId)
  }, [resolvedSessionId, sessionId, boundToChat])

  // The thread a turn should resolve to before creating a new one. When bound to
  // a chat session we never fall back to the global most-recent thread.
  const baseSessionId = () => sessionId ?? (boundToChat ? null : resolvedSessionId)

  // Create a fresh discovery thread and, when bound, write its id back onto the
  // chat session so a later reload resumes this exact thread. Binding is
  // best-effort — a failure never blocks the turn.
  const createThread = async (): Promise<string> => {
    // Each bound chat session gets its OWN fresh discovery thread, so sessions are
    // independent conversations instead of all sharing one "unified" thread. The
    // student's goals/needs/identity profile still aggregates globally (per
    // student_id), so matching/recommendations are unaffected.
    const created = await startUnifiedSession(boundToChat)
    qc.invalidateQueries({ queryKey: ['discovery', 'sessions', 'unified'] })
    if (boundToChat && chatSessionId) {
      try {
        await updateChatSession(chatSessionId, { conversation_session_id: created.id })
        qc.invalidateQueries({ queryKey: ['chat-tree'] })
      } catch {
        // non-fatal: the turn proceeds; binding will retry on the next thread.
      }
    }
    return created.id
  }

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

  // Guided journey state (stages + matches unlock) + per-turn guidance derived
  // from the latest assistant turn's structured signals (LLM-suggested chips and
  // the orchestrator's offer-to-advance). All no-ops when not guided.
  const journey = useJourneyState(guided)
  const lastMsg = messages.length ? messages[messages.length - 1] : undefined
  const lastSignals =
    lastMsg?.role === 'assistant'
      ? (lastMsg.extracted_signals as Record<string, unknown> | null)
      : null
  const llmChips = Array.isArray(lastSignals?.suggested_options)
    ? (lastSignals.suggested_options as string[]).filter(s => typeof s === 'string' && s.trim())
    : []
  // "Limited mode" — Uni is answering from the canned / rule-based fallback rather
  // than the live AI (todo 2.5). The backend stamps this on the assistant turn's
  // signals (orchestrator degraded path); a mid-stream streaming failure flips the
  // local flag. Either way the student is told, instead of degrading silently.
  const limitedMode =
    streamDegraded ||
    lastSignals?._mode === 'rule_based' ||
    lastSignals?._phase === 'A2_error'
  // Phase 2 affordance hint — render the options as multi-select or a 1–5
  // importance slider when the orchestrator asks for it; default single-choice.
  const sugInput = (lastSignals?.suggested_input ?? null) as
    | { kind?: string; low_label?: string; high_label?: string }
    | null
  const answerKind: 'choice' | 'multi' | 'scale' =
    sugInput?.kind === 'multi' || sugInput?.kind === 'scale' ? sugInput.kind : 'choice'
  // Earned Continue: the orchestrator can proactively offer to advance
  // (`requested_layer_advance`), but readiness is ultimately driven by the
  // engine's per-layer completion (spec §4). When the deterministic handoff
  // verdict says all Discovery layers are covered, surface Continue even if the
  // assistant turn omitted the tool flag (rule-based fallback, streaming error,
  // or a model that narrates readiness without calling it).
  const offeredAdvance =
    guided &&
    !isEmpty &&
    (lastSignals?.requested_layer_advance === true || journey.matchesUnlocked)
  const curIdx = journey.stages.findIndex(s => s.state === 'current')
  const nextStageLabel =
    journey.matchesUnlocked || curIdx < 0
      ? 'your matches'
      : (journey.stages[curIdx + 1]?.label ?? 'your matches')

  const turnMut = useMutation({
    mutationFn: async (content: string) => {
      // Reuse the session already loaded from listSessions before creating a new
      // one — relying solely on `sessionId` state can race the effect that binds
      // it, splitting the conversation across two sessions.
      let sid = baseSessionId()
      if (!sid) sid = await createThread()
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
  }, [messages.length, turnMut.isPending, streaming, streamText])

  // The persistent composer orb — Uni's living presence (chat-tab spec §1). A
  // transient `celebrating` fires once on the false→true edge of matchesUnlocked
  // (a real milestone); the rest is derived from existing turn state.
  const [celebrating, setCelebrating] = useState(false)
  const prevMatchesUnlocked = useRef(journey.matchesUnlocked)
  useEffect(() => {
    if (journey.matchesUnlocked && !prevMatchesUnlocked.current) {
      setCelebrating(true)
      const t = setTimeout(() => setCelebrating(false), 2000)
      prevMatchesUnlocked.current = journey.matchesUnlocked
      return () => clearTimeout(t)
    }
    prevMatchesUnlocked.current = journey.matchesUnlocked
  }, [journey.matchesUnlocked])
  const composerOrbState = deriveComposerOrbState({
    streaming,
    streamText,
    pending: turnMut.isPending,
    draft,
    celebrating,
  })

  const refreshAfterTurn = async (sid: string) => {
    await qc.invalidateQueries({ queryKey: ['discovery', 'session', sid] })
    qc.invalidateQueries({ queryKey: ['discovery', 'completion'] })
    qc.invalidateQueries({ queryKey: ['discovery', 'handoff'] })
    qc.invalidateQueries({ queryKey: ['discovery', 'livingProfile'] })
    qc.invalidateQueries({ queryKey: ['goals'] })
    qc.invalidateQueries({ queryKey: ['needs'] })
    qc.invalidateQueries({ queryKey: ['identity'] })
  }

  // Stream a turn over SSE (Spec 77 §6). Mirrors turnMut but renders Uni's reply
  // token-by-token. On any connection failure with no persisted student echo it
  // falls back to the non-streaming mutation (no duplicate turn).
  const sendStreaming = async (text: string) => {
    let sid = baseSessionId()
    let studentEchoed = false
    let finished = false
    setStreaming(true)
    setStreamDegraded(false)
    setStreamText('')
    setStreamStudent({
      id: '__pending__',
      session_id: sid ?? '',
      role: 'student',
      content: text,
      extracted_signals: null,
      created_at: new Date().toISOString(),
    } as DiscoveryMessage)
    setDraft('')
    const ctrl = new AbortController()
    streamAbort.current = ctrl
    const finish = async () => {
      if (finished) return
      finished = true
      setHandoffDismissed(false)
      if (sid) await refreshAfterTurn(sid)
      setStreaming(false)
      setStreamStudent(null)
      setStreamText('')
    }
    try {
      if (!sid) sid = await createThread()
      if (sid !== sessionId) setSessionId(sid)
      await streamDiscoveryMessage(
        sid,
        { role: 'student', content: text },
        {
          onStudentMessage: msg => {
            studentEchoed = true
            setStreamStudent(msg)
          },
          onDelta: t => setStreamText(prev => prev + t),
          onAssistantMessage: msg => {
            if (msg?.content) setStreamText(msg.content)
          },
          onError: m => {
            setStreamDegraded(true)
            showToast(m || 'Could not send message.', 'error')
          },
          onDone: () => {
            void finish()
          },
        },
        ctrl.signal,
      )
      await finish()
    } catch (e) {
      if (ctrl.signal.aborted) return
      setStreaming(false)
      setStreamStudent(null)
      setStreamText('')
      if (sid && !studentEchoed) {
        turnMut.mutate(text)
      } else if (sid) {
        setStreamDegraded(true)
        await refreshAfterTurn(sid)
        showToast('Connection interrupted — your message was saved.', 'info')
      } else {
        showToast((e as Error).message || 'Could not send message.', 'error')
      }
    }
  }

  const send = (content: string) => {
    const text = content.trim()
    if (!text) return
    // Wait for the sessions query to settle so we don't spawn a duplicate
    // session while an existing one is still loading. Surface a toast instead of
    // dropping the message silently (e.g. a profile-drawer gap invitation tapped
    // while Uni is still replying), so it never looks accepted-but-ignored.
    if (turnMut.isPending || streaming || sessionsLoading) {
      showToast(
        turnMut.isPending || streaming
          ? 'Uni is still replying — try again in a moment.'
          : 'One moment — still getting set up…',
        'info',
      )
      return
    }
    if (canStream) void sendStreaming(text)
    else turnMut.mutate(text)
  }

  // Expose an imperative `ask` (stable identity) so the rail can drive the
  // conversation — revisit a stage, accept a gap invitation, open matches.
  const sendRef = useRef(send)
  sendRef.current = send
  useEffect(() => {
    onReady?.({ ask: (t: string) => sendRef.current(t) })
  }, [onReady])

  // Cross-sell prefill (e.g. "Ask counselor" on a program): DiscoverHomePage read
  // it off /s?prefill=… and handed it down. Send it as the opening student turn
  // once the session has resolved — and claim the opener slot so Uni answers the
  // question directly instead of greeting generically. Fires once; works in both
  // stream and non-stream (reduced-motion) modes, unlike the opener. Declared
  // before the opener effect so it runs first within a commit.
  const prefillFired = useRef(false)
  useEffect(() => {
    if (prefillFired.current) return
    const q = prefill?.trim()
    if (!q) return
    if (sessionsLoading) return // wait for the active session to resolve
    if (!boundToChat && resolvedSessionId && !detail) return // wait for the global thread's messages (bound chat sessions use their own thread, so don't block on it)
    if (streaming || turnMut.isPending) return // don't fight an in-flight turn
    prefillFired.current = true
    openerFired.current = true // Uni answers the question instead of the greeting
    sendRef.current(q)
  }, [prefill, sessionsLoading, resolvedSessionId, detail, streaming, turnMut.isPending])

  // Uni speaks first — stream the proactive opener (no student bubble). On
  // failure, fall back to the static greeting.
  const sendOpener = async () => {
    let sid = baseSessionId()
    let finished = false
    setStreaming(true)
    setStreamText('')
    const ctrl = new AbortController()
    streamAbort.current = ctrl
    const finish = async () => {
      if (finished) return
      finished = true
      setHandoffDismissed(false)
      if (sid) await refreshAfterTurn(sid)
      setStreaming(false)
      setStreamText('')
    }
    try {
      if (!sid) sid = await createThread()
      if (sid !== sessionId) setSessionId(sid)
      await streamDiscoveryOpener(
        {
          onDelta: t => setStreamText(prev => prev + t),
          onAssistantMessage: msg => {
            if (msg?.content) setStreamText(msg.content)
          },
          onError: () => setOpenerFailed(true),
          onDone: () => {
            void finish()
          },
        },
        ctrl.signal,
      )
      await finish()
    } catch {
      if (ctrl.signal.aborted) return
      setStreaming(false)
      setStreamText('')
      setOpenerFailed(true) // show the static greeting instead
      if (sid) await refreshAfterTurn(sid)
    }
  }
  const sendOpenerRef = useRef(sendOpener)
  sendOpenerRef.current = sendOpener
  // Fire once, when the conversation is confirmed empty and streaming is
  // available. A returning student with messages never triggers it.
  useEffect(() => {
    if (openerFired.current) return
    if (prefill?.trim() && !prefillFired.current) return // let the prefill drive, not a greeting
    if (sessionsLoading) return // wait for the active session to resolve
    if (!boundToChat && resolvedSessionId && !detail) return // wait for the global thread's messages (bound chat sessions use their own thread, so don't block on it)
    if (!isEmpty || streaming || turnMut.isPending) return
    if (!canStream) return // reduced-motion / no-stream → static greeting stands
    openerFired.current = true
    void sendOpenerRef.current()
  }, [prefill, sessionsLoading, resolvedSessionId, detail, isEmpty, streaming, turnMut.isPending, canStream])

  return (
    <div className="flex flex-col h-full min-h-[520px] max-w-[640px] mx-auto w-full">
      {guided && !isEmpty && journey.currentStage && (
        <div className="mb-3 border-b border-border pb-3">
          <div className="flex items-center justify-between">
            <span className="text-sm font-semibold text-foreground">
              {journey.currentStage.label}
            </span>
            <span className="text-eyebrow text-muted-foreground">Discovery</span>
          </div>
          <div className="mt-2 h-1 w-full rounded-full bg-muted overflow-hidden">
            <div
              className="h-full bg-secondary transition-all"
              style={{ width: `${Math.round((journey.currentStage.pct || 0) * 100)}%` }}
            />
          </div>
        </div>
      )}
      <div
        ref={scrollRef}
        // stagger-list (Ship B): each bubble fades/rises on mount — newly
        // appended messages animate once; a history load cascades the first six
        // then renders the rest together instead of replaying every bubble.
        className="stagger-list flex-1 overflow-y-auto space-y-3.5 pr-1 pb-3"
        aria-live="polite"
        aria-label="Conversation with Uni"
      >
        {isEmpty && !streamText && (!canStream || openerFailed) ? (
          // Fallback greeting — shown ONLY when the proactive opener can't stream
          // (reduced motion / no ReadableStream) or it failed AND streamed nothing.
          // The extra `!streamText` guard prevents a double-greeting (todo 2.2): a
          // partially-streamed-then-failed opener keeps its partial text instead of
          // ALSO rendering this static line. Normally Uni's dynamic opener streams in.
          <div className="flex gap-2.5 py-6">
            <UniOrb className="mt-0.5" />
            <div className="pt-0.5 text-sm leading-relaxed text-foreground max-w-[80%]">
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
        {/* Inline enrich widget — surfaces the next Prompt-Library prompt as a
            structured card in the thread. Only shown when the conversation has
            at least one message, Uni is idle (not streaming), and the profile
            still has signals to fill (EnrichWidget self-renders null otherwise).
            Placed before the streaming bubbles so it scrolls out of view
            naturally as new messages arrive. */}
        {!isEmpty && !streaming && !turnMut.isPending && (
          <InlineChatEnrichCard />
        )}

        {/* In-flight streaming turn (Spec 77 §6) — optimistic student + live reply. */}
        {streaming && streamStudent && <UniBubble message={streamStudent} />}
        {streaming && streamText && (
          <div className="flex justify-start gap-2.5">
            <UniOrb state="responding" className="mt-0.5" />
            <div className="pt-0.5 text-sm whitespace-pre-wrap break-words max-w-[80%] leading-relaxed text-foreground">
              {streamText}
              <span className="ml-0.5 inline-block h-3.5 w-px align-middle bg-secondary motion-safe:animate-pulse" />
            </div>
          </div>
        )}

        {(turnMut.isPending ||
          (streaming && !streamText) ||
          (isEmpty && canStream && !openerFailed && !streamText)) && (
          <div className="flex items-center justify-start gap-2.5">
            <UniOrb state="thinking" />
            <span className="inline-flex gap-1 pt-0.5">
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
        )}

        {!isEmpty && !handoffDismissed && !streaming && (
          <FirstLookCard variant="always" onKeepTalking={() => setHandoffDismissed(true)} />
        )}
      </div>

      {offeredAdvance && !turnMut.isPending && !streaming && (
        <div className="mb-2 flex justify-end">
          <Button
            variant="secondary"
            size="sm"
            onClick={() => send(`Let's move on to ${nextStageLabel}.`)}
          >
            Continue to {nextStageLabel} →
          </Button>
        </div>
      )}
      {!turnMut.isPending &&
        !streaming &&
        llmChips.length > 0 && (
          // Reply chips come ONLY from Uni's own suggested options (todo 2.3) — no
          // hard-coded "phone-menu" fallbacks. When the AI offers none, the row is
          // simply absent and the student types or uses the inline enrich card.
          <AnswerChoices
            options={llmChips}
            onPick={send as (v: string | string[]) => void}
            kind={answerKind}
            lowLabel={sugInput?.low_label}
            highLabel={sugInput?.high_label}
          />
        )}

      {showUpload && (
        <div className="mb-2">
          <MaterialUpload
            onApplied={result => {
              const n = Object.values(result.counts || {}).reduce((a, b) => a + b, 0)
              void qc.invalidateQueries({ queryKey: ['discovery', 'livingProfile'] })
              void qc.invalidateQueries({ queryKey: ['goals'] })
              void qc.invalidateQueries({ queryKey: ['needs'] })
              void qc.invalidateQueries({ queryKey: ['identity'] })
              showToast(`Added ${n} items from your file to My Space.`, 'success')
              setShowUpload(false)
            }}
          />
        </div>
      )}

      {limitedMode && (
        <div
          role="status"
          className="mb-2 rounded-lg border border-amber-500/30 bg-amber-500/5 px-3 py-2 text-xs text-muted-foreground"
        >
          Limited mode — Uni is replying from saved guidance for now. Your messages are
          still saved, and full answers resume automatically.
        </div>
      )}

      <form
        onSubmit={e => {
          e.preventDefault()
          send(draft)
        }}
        className="flex items-end gap-2 border-t border-border pt-3"
      >
        {/* Uni's persistent living presence — reflects listening / thinking /
            responding / celebrating; still at idle (chat-tab spec §1). */}
        <UniOrb state={composerOrbState} size={24} className="mb-1.5 shrink-0" />
        <Button
          type="button"
          variant="ghost"
          size="sm"
          onClick={() => setShowUpload(v => !v)}
          aria-label="Upload a file for Uni to read"
          aria-pressed={showUpload}
        >
          <Paperclip size={16} />
        </Button>
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
          disabled={turnMut.isPending || streaming}
        />
        <Button
          type="submit"
          variant="secondary"
          size="sm"
          loading={turnMut.isPending || streaming}
          disabled={!draft.trim() || streaming}
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
