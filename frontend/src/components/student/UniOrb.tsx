/**
 * UniOrb — Uni's presence. The single brand element for the AI identity.
 *
 * Spec: docs/superpowers/specs/2026-06-19-uni-chat-tab-redesign-design.md §1
 *
 * An aura orb: a radial-gradient gold→cobalt disc (the ONE sanctioned gradient;
 * the brand's "no gradients" rule is waived only for Uni). There is NO name
 * label and NO avatar/monogram — the orb IS Uni.
 *
 * Motion = meaning. **Idle is completely still** (no breathing at rest) so the
 * surface feels calm until something happens; motion appears only with activity.
 * Each state is a distinct, brand-faithful animation (see index.css `.uni-orb`).
 * Activity animations are gated behind `prefers-reduced-motion: no-preference`,
 * so reduced-motion users get a calm static orb (state still reads via the
 * gradient + the error desaturation).
 */
import clsx from 'clsx'

export type OrbState =
  | 'idle' // still
  | 'listening' // gentle slow pulse (user typing)
  | 'thinking' // faster breathe + gold pulse-ring
  | 'responding' // medium breathe while text streams
  | 'reading' // a light scan sweeps the orb (ingesting an upload)
  | 'saved' // brief green flash
  | 'celebrating' // gold sparkle — real milestones only
  | 'clarifying' // a soft wobble (asking a follow-up)
  | 'error' // desaturates, calm and courteous

export default function UniOrb({
  state = 'idle',
  size = 28,
  className,
}: {
  state?: OrbState
  /** Diameter in px. Defaults to 28 (matches the conversation turn mark). */
  size?: number
  className?: string
}) {
  return (
    <div
      className={clsx('uni-orb', `uni-orb--${state}`, className)}
      style={{ width: size, height: size }}
      role="img"
      aria-label="Uni"
    >
      <span className="uni-orb__core" />
      {state === 'thinking' && <span className="uni-orb__ring" aria-hidden />}
      {state === 'reading' && <span className="uni-orb__scan" aria-hidden />}
      {state === 'celebrating' && <span className="uni-orb__sparkle" aria-hidden />}
    </div>
  )
}
