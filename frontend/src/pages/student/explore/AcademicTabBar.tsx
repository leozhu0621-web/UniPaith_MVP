// Academic sub-tabs (Spec 2026-06-14 restructure) — Universities · Updates ·
// Events, driven by the ?sub= param. Universities = program search + schools
// browse; Updates / Events = news from the schools you follow.
import { useRef } from 'react'
import { Building2, CalendarDays, Newspaper, type LucideIcon } from 'lucide-react'

export type AcademicSub = 'universities' | 'updates' | 'events'
export const ACADEMIC_SUBS: readonly AcademicSub[] = ['universities', 'updates', 'events'] as const

const SUBS: { key: AcademicSub; label: string; icon: LucideIcon }[] = [
  { key: 'universities', label: 'Universities', icon: Building2 },
  { key: 'updates', label: 'Updates', icon: Newspaper },
  { key: 'events', label: 'Events', icon: CalendarDays },
]

export function normalizeAcademicSub(raw: string | null): AcademicSub {
  return raw && (ACADEMIC_SUBS as readonly string[]).includes(raw) ? (raw as AcademicSub) : 'universities'
}

export default function AcademicTabBar({
  sub,
  onChange,
  badges,
}: {
  sub: AcademicSub
  onChange: (s: AcademicSub) => void
  badges?: Partial<Record<AcademicSub, number>>
}) {
  const ref = useRef<HTMLDivElement>(null)
  const onKeyDown = (e: React.KeyboardEvent<HTMLButtonElement>, idx: number) => {
    const btns = ref.current?.querySelectorAll<HTMLButtonElement>('[role="tab"]')
    if (!btns) return
    let next = -1
    if (e.key === 'ArrowRight') next = (idx + 1) % btns.length
    else if (e.key === 'ArrowLeft') next = (idx - 1 + btns.length) % btns.length
    else if (e.key === 'Home') next = 0
    else if (e.key === 'End') next = btns.length - 1
    if (next >= 0) {
      e.preventDefault()
      btns[next].focus()
      onChange(SUBS[next].key)
    }
  }

  return (
    <div ref={ref} role="tablist" aria-label="Academic sections" className="mb-5 flex gap-1.5 overflow-x-auto no-scrollbar">
      {SUBS.map((s, idx) => {
        const Icon = s.icon
        const active = sub === s.key
        const badge = badges?.[s.key] ?? 0
        return (
          <button
            key={s.key}
            role="tab"
            aria-selected={active}
            tabIndex={active ? 0 : -1}
            onClick={() => onChange(s.key)}
            onKeyDown={e => onKeyDown(e, idx)}
            className={`inline-flex items-center gap-1.5 whitespace-nowrap rounded-full border px-3.5 py-1.5 text-sm font-medium transition-colors ${
              active
                ? 'border-secondary bg-secondary/10 text-secondary'
                : 'border-border text-muted-foreground hover:text-foreground'
            }`}
          >
            <Icon size={14} aria-hidden />
            {s.label}
            {badge > 0 && (
              <span className="min-w-[16px] h-4 px-1 inline-flex items-center justify-center rounded-full bg-secondary text-secondary-foreground text-[9px] font-bold leading-none">
                {badge > 9 ? '9+' : badge}
              </span>
            )}
          </button>
        )
      })}
    </div>
  )
}
