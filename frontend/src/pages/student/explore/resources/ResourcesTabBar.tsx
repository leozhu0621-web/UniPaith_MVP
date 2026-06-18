// Resources sub-tab bar (Spec 2026-06-14) — Universities · Financial ·
// International, driven by the ?sub= param. ARIA tablist with arrow-key nav,
// mirroring DiscoverTabBar.
import { useRef } from 'react'
import { Building2, Banknote, Globe2, type LucideIcon } from 'lucide-react'

export type ResourcesSub = 'universities' | 'financial' | 'international'
export const RESOURCES_SUBS: readonly ResourcesSub[] = ['universities', 'financial', 'international'] as const

const SUBS: { key: ResourcesSub; label: string; icon: LucideIcon }[] = [
  { key: 'universities', label: 'Universities', icon: Building2 },
  { key: 'financial', label: 'Financial', icon: Banknote },
  { key: 'international', label: 'International', icon: Globe2 },
]

export function normalizeSub(raw: string | null): ResourcesSub {
  return raw && (RESOURCES_SUBS as readonly string[]).includes(raw) ? (raw as ResourcesSub) : 'universities'
}

export default function ResourcesTabBar({
  sub,
  onChange,
}: {
  sub: ResourcesSub
  onChange: (s: ResourcesSub) => void
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
    <div ref={ref} role="tablist" aria-label="Resources sections" className="mb-5 flex gap-1.5 overflow-x-auto no-scrollbar">
      {SUBS.map((s, idx) => {
        const Icon = s.icon
        const active = sub === s.key
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
          </button>
        )
      })}
    </div>
  )
}
