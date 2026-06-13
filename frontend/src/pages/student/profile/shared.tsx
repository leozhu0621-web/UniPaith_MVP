/**
 * Universal Profile — shared building blocks (Spec/08-universal-profile.md).
 *
 * Completion model, the brand completion ring (§3), section headers, the
 * autosave "Saved" indicator (§19), and the relative-time copy strings (§24).
 * Everything here is token-only and Europa — no raw hex, no legacy aliases.
 */
import { useEffect, useRef, useState } from 'react'
import clsx from 'clsx'

import ConfidenceDots from '../../../components/ui/ConfidenceDots'

// ── Relative-time copy (§24: "just now" / "2h ago" / "2 days ago") ──────────
export function relativeShort(iso: string | null | undefined): string | null {
  if (!iso) return null
  const then = new Date(iso).getTime()
  if (Number.isNaN(then)) return null
  const secs = Math.max(0, Math.round((Date.now() - then) / 1000))
  if (secs < 45) return 'just now'
  const mins = Math.round(secs / 60)
  if (mins < 60) return `${mins}m ago`
  const hrs = Math.round(mins / 60)
  if (hrs < 24) return `${hrs}h ago`
  const days = Math.round(hrs / 24)
  if (days < 30) return `${days} ${days === 1 ? 'day' : 'days'} ago`
  const months = Math.round(days / 30)
  if (months < 12) return `${months} ${months === 1 ? 'month' : 'months'} ago`
  const years = Math.round(months / 12)
  return `${years} ${years === 1 ? 'year' : 'years'} ago`
}

export function lastUpdatedLabel(iso: string | null | undefined): string {
  const rel = relativeShort(iso)
  return rel ? `Last updated ${rel}` : 'Not started'
}

// ── Completion model ────────────────────────────────────────────────────────
export type CategoryKey =
  | 'personal'
  | 'identity'
  | 'academics'
  | 'experience'
  | 'goals'
  | 'needs'
  | 'strategy'
  | 'preparation'
  | 'preferences'
  | 'financial'

export interface CategoryStat {
  key: CategoryKey
  label: string
  /** Profile tab this cluster opens. */
  tab: string
  /** 0–100 completion. */
  pct: number
  /** 0–5 filled dots (spec §4 5-dot indicator). */
  dots: number
  lastUpdated: string | null
}

export const CATEGORY_META: { key: CategoryKey; label: string; tab: string; hint: string }[] = [
  { key: 'personal', label: 'Personal', tab: 'overview', hint: 'Unlocks your personalised program intro on match cards.' },
  { key: 'identity', label: 'Identity', tab: 'identity', hint: 'Unlocks values-based match rationales and the AI summary.' },
  { key: 'academics', label: 'Academics', tab: 'academics', hint: 'Unlocks fitness score improvements and transcript comparisons.' },
  { key: 'experience', label: 'Experience', tab: 'experience', hint: 'Unlocks activity and research signal in match scoring.' },
  { key: 'goals', label: 'Goals', tab: 'goals', hint: 'Unlocks Strategy generation and goal-aligned match filters.' },
  { key: 'needs', label: 'Needs', tab: 'needs', hint: 'Unlocks need-aware filtering (support services, campus culture).' },
  { key: 'strategy', label: 'Strategy', tab: 'strategy', hint: 'Unlocks the broad-strategy view on your Discover page.' },
  { key: 'preparation', label: 'Preparation', tab: 'preparation', hint: 'Unlocks document-based completeness checks before applying.' },
  { key: 'preferences', label: 'Preferences', tab: 'preferences', hint: 'Unlocks location, size, and format filters in Discover.' },
  { key: 'financial', label: 'Financial', tab: 'financial', hint: 'Unlocks net-cost comparisons and aid-likelihood signals.' },
]

function maxDate(...isos: (string | null | undefined)[]): string | null {
  const valid = isos.filter(Boolean) as string[]
  if (valid.length === 0) return null
  return valid.reduce((a, b) => (new Date(a) > new Date(b) ? a : b))
}

function latestOf(items: { updated_at?: string; created_at?: string }[]): string | null {
  return maxDate(...items.flatMap(i => [i.updated_at, i.created_at]))
}

function pctToDots(pct: number): number {
  return Math.max(0, Math.min(5, Math.round((pct / 100) * 5)))
}

export interface CompletionInputs {
  profile: any
  documents: any[]
  workExperiences: any[]
  competitions: any[]
  accommodations: any
  scheduling: any
  preferences: any
  dataConsent: any
  identity?: any
  goals?: any[]
  needs?: any[]
  strategy?: any
}

/** Compute the per-cluster completion stats shown on the Overview map. */
export function computeCategoryStats(input: CompletionInputs): CategoryStat[] {
  const p = input.profile ?? {}
  const ratio = (filled: number, total: number) => (total === 0 ? 0 : Math.round((filled / total) * 100))

  // personal
  const personalFields = [
    p.first_name,
    p.last_name,
    p.date_of_birth,
    p.nationality,
    p.country_of_residence,
    p.bio_text,
  ]
  const personalPct = ratio(personalFields.filter(Boolean).length, personalFields.length)

  // identity
  const id = input.identity
  const identityFilled = id
    ? [id.core_values?.length, id.worldview?.length, id.self_awareness?.length, id.identity_summary].filter(
        v => (typeof v === 'number' ? v > 0 : Boolean(v)),
      ).length
    : 0
  const identityPct = ratio(identityFilled, 4)

  // academics
  const acadSub = [
    (p.academic_records ?? []).length > 0,
    (p.test_scores ?? []).length > 0,
    (p.languages ?? []).length > 0,
    (p.research_entries ?? []).length > 0,
  ]
  const academicsPct = ratio(acadSub.filter(Boolean).length, acadSub.length)

  // experience
  const expSub = [
    (p.activities ?? []).length > 0,
    input.workExperiences.length > 0,
    input.competitions.length > 0,
    (p.portfolio_items ?? []).length > 0,
    (p.online_presence ?? []).length > 0,
  ]
  const experiencePct = ratio(expSub.filter(Boolean).length, expSub.length)

  // goals — one per category counts toward completeness
  const goalCats = new Set((input.goals ?? []).map(g => g.category))
  const goalsPct = ratio(goalCats.size, 3)

  // needs — covered Maslow levels (5 levels)
  const needLevels = new Set((input.needs ?? []).map(n => n.maslow_level))
  const needsPct = ratio(needLevels.size, 5)

  // strategy
  const st = input.strategy
  const strategyFilled = st
    ? [st.career_target, st.target_degree, (st.academic_path ?? []).length, st.narrative].filter(v =>
        typeof v === 'number' ? v > 0 : Boolean(v),
      ).length
    : 0
  const strategyPct = ratio(strategyFilled, 4)

  // preparation
  const prepSub = [
    input.documents.length > 0,
    Boolean(input.accommodations),
    Boolean(input.scheduling),
  ]
  const preparationPct = ratio(prepSub.filter(Boolean).length, prepSub.length)

  // preferences
  const prefs = input.preferences
  const prefFields = prefs
    ? [
        prefs.preferred_countries?.length,
        prefs.preferred_city_size,
        prefs.program_size_preference,
        prefs.target_degree_level,
      ].filter(v => (typeof v === 'number' ? v > 0 : Boolean(v))).length
    : 0
  const preferencesPct = ratio(prefFields, 4)

  // financial
  const finFields = prefs
    ? [prefs.budget_min != null || prefs.budget_max != null, Boolean(prefs.funding_requirement)].filter(
        Boolean,
      ).length
    : 0
  const financialPct = ratio(finFields, 2)

  const lastByKey: Record<CategoryKey, string | null> = {
    personal: p.updated_at ?? null,
    identity: id?.updated_at ?? null,
    academics: maxDate(
      latestOf(p.academic_records ?? []),
      latestOf(p.test_scores ?? []),
      latestOf(p.languages ?? []),
      latestOf(p.research_entries ?? []),
    ),
    experience: maxDate(
      latestOf(p.activities ?? []),
      latestOf(input.workExperiences),
      latestOf(input.competitions),
      latestOf(p.portfolio_items ?? []),
      latestOf(p.online_presence ?? []),
    ),
    goals: latestOf(input.goals ?? []),
    needs: latestOf(input.needs ?? []),
    strategy: st?.updated_at ?? null,
    preparation: maxDate(
      latestOf(input.documents),
      input.accommodations?.updated_at,
      input.scheduling?.updated_at,
    ),
    preferences: prefs?.updated_at ?? null,
    financial: prefs?.updated_at ?? null,
  }

  const pctByKey: Record<CategoryKey, number> = {
    personal: personalPct,
    identity: identityPct,
    academics: academicsPct,
    experience: experiencePct,
    goals: goalsPct,
    needs: needsPct,
    strategy: strategyPct,
    preparation: preparationPct,
    preferences: preferencesPct,
    financial: financialPct,
  }

  return CATEGORY_META.map(m => ({
    key: m.key,
    label: m.label,
    tab: m.tab,
    pct: pctByKey[m.key],
    dots: pctToDots(pctByKey[m.key]),
    lastUpdated: lastByKey[m.key],
  }))
}

export function overallPct(stats: CategoryStat[]): number {
  if (stats.length === 0) return 0
  return Math.round(stats.reduce((sum, s) => sum + s.pct, 0) / stats.length)
}

// ── Brand completion ring (§3: 64px gold donut, --border track) ─────────────
export function CompletionRing({
  value,
  size = 64,
  stroke = 6,
  label = 'Complete',
}: {
  value: number
  size?: number
  stroke?: number
  label?: string
}) {
  const v = Math.max(0, Math.min(100, value))
  const r = (size - stroke) / 2
  const c = 2 * Math.PI * r
  const offset = c - (v / 100) * c
  return (
    <div className="relative flex-shrink-0" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90" viewBox={`0 0 ${size} ${size}`}>
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="hsl(var(--border))" strokeWidth={stroke} />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          stroke="hsl(var(--primary))"
          strokeWidth={stroke}
          strokeDasharray={c}
          strokeDashoffset={offset}
          strokeLinecap="round"
          className="transition-[stroke-dashoffset] duration-700 ease-out"
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center leading-none">
        <span className="font-bold text-foreground" style={{ fontSize: size * 0.26 }}>
          {Math.round(v)}%
        </span>
        {label && size >= 72 && (
          <span className="text-[10px] text-muted-foreground mt-0.5">{label}</span>
        )}
      </div>
    </div>
  )
}

export { ConfidenceDots }

// ── Section header (eyebrow optional + H3 + action + save status) ────────────
export function SectionHeader({
  title,
  description,
  action,
  saveState,
  refEl,
}: {
  title: string
  description?: string
  action?: React.ReactNode
  saveState?: SaveState
  refEl?: React.Ref<HTMLDivElement>
}) {
  return (
    <div ref={refEl} className="flex items-start justify-between gap-3 mb-3">
      <div className="min-w-0">
        <div className="flex items-center gap-2">
          <h3 className="text-h3 text-foreground">{title}</h3>
          {saveState && <SaveStatus state={saveState} />}
        </div>
        {description && <p className="text-sm text-muted-foreground mt-0.5">{description}</p>}
      </div>
      {action && <div className="shrink-0">{action}</div>}
    </div>
  )
}

// ── Autosave indicator (§19: "Saving…" → "Saved at 14:32" → fade) ───────────
export type SaveState = 'idle' | 'saving' | 'saved' | 'error'

export function SaveStatus({ state }: { state: SaveState }) {
  // Capture the wall-clock time at the moment we transition INTO 'saved', not
  // on every render — otherwise "Saved at HH:MM" drifts forward each re-render.
  const [savedAt, setSavedAt] = useState<string | null>(null)
  useEffect(() => {
    if (state === 'saved') {
      setSavedAt(
        new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: false }),
      )
    }
  }, [state])

  if (state === 'idle') return null
  if (state === 'saving') return <span className="text-xs text-muted-foreground">Saving…</span>
  if (state === 'error')
    return <span className="text-xs text-error">Couldn't save. Try again.</span>
  return <span className="text-xs text-success">Saved at {savedAt ?? '—'}</span>
}

/**
 * Debounced autosave (§19, §10). Calls `save` 800ms after `value` settles.
 * Skips the initial mount so loading data doesn't trigger a write.
 *
 * Ship D (input preservation): a pending debounce is FLUSHED on unmount —
 * switching tabs inside the 800ms window still writes the edit instead of
 * silently dropping it.
 */
export function useAutosave<T>(
  value: T,
  save: (v: T) => Promise<unknown>,
  { delay = 800, enabled = true }: { delay?: number; enabled?: boolean } = {},
) {
  const [state, setState] = useState<SaveState>('idle')
  const mounted = useRef(false)
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null)
  const latest = useRef(value)
  latest.current = value
  // True while an edit is scheduled but not yet handed to `save`.
  const pending = useRef(false)
  const saveRef = useRef(save)
  saveRef.current = save

  useEffect(() => {
    if (!mounted.current) {
      mounted.current = true
      return
    }
    if (!enabled) return
    if (timer.current) clearTimeout(timer.current)
    setState('saving')
    pending.current = true
    timer.current = setTimeout(() => {
      pending.current = false
      save(latest.current)
        .then(() => {
          setState('saved')
          setTimeout(() => setState(s => (s === 'saved' ? 'idle' : s)), 2200)
        })
        .catch(() => setState('error'))
    }, delay)
    return () => {
      if (timer.current) clearTimeout(timer.current)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [JSON.stringify(value), enabled])

  // Unmount flush — fire-and-forget the last unsaved value (no setState here;
  // the component is gone, the write is what matters).
  useEffect(
    () => () => {
      if (pending.current) {
        pending.current = false
        void saveRef.current(latest.current).catch(() => {})
      }
    },
    [],
  )

  return state
}

// ── Toggle switch (token-only) ──────────────────────────────────────────────
export function Toggle({
  checked,
  onChange,
  disabled,
  id,
}: {
  checked: boolean
  onChange: (v: boolean) => void
  disabled?: boolean
  id?: string
}) {
  return (
    <button
      type="button"
      role="switch"
      id={id}
      aria-checked={checked}
      disabled={disabled}
      onClick={() => onChange(!checked)}
      className={clsx(
        'relative inline-flex h-6 w-11 shrink-0 items-center rounded-pill transition-colors duration-200',
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-1 focus-visible:ring-offset-background',
        'disabled:opacity-50 disabled:cursor-not-allowed',
        checked ? 'bg-secondary' : 'bg-border',
      )}
    >
      <span
        className={clsx(
          'inline-block h-5 w-5 transform rounded-full bg-card shadow transition-transform duration-200',
          checked ? 'translate-x-5' : 'translate-x-0.5',
        )}
      />
    </button>
  )
}
