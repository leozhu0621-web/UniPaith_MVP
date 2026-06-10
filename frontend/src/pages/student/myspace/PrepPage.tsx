import { useState, useEffect, useRef, lazy, Suspense } from 'react'
import { useSearchParams, useNavigate } from 'react-router-dom'
import { GraduationCap, NotebookPen } from 'lucide-react'

// My Space › Prep (Spec 2026-06-10 §5) — the preparation room. Ship 2 gathers
// Workshops + Prompts here (from /s/manage); Ship 3 adds Interviews,
// Recommenders and Documents. Workshops stay feedback-only by spec.

const WorkshopsTab = lazy(() => import('../apply/WorkshopsTab'))
const PromptLibraryTab = lazy(() => import('../apply/promptlibrary/PromptLibraryTab'))

type Tab = 'workshops' | 'prompts'

const TABS: { key: Tab; label: string; icon: typeof GraduationCap }[] = [
  { key: 'workshops', label: 'Workshops', icon: GraduationCap },
  { key: 'prompts', label: 'Prompts', icon: NotebookPen },
]

export default function PrepPage() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const rawTab = searchParams.get('tab') as Tab | null
  const [tab, setTab] = useState<Tab>(rawTab && TABS.some(t => t.key === rawTab) ? rawTab : 'workshops')
  const tablistRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (rawTab && TABS.some(t => t.key === rawTab) && rawTab !== tab) setTab(rawTab)
  }, [rawTab, tab])

  const switchTab = (t: Tab) => {
    setTab(t)
    // Preserve deep-link params other than tab (e.g. prompts ?view=major).
    const params = new URLSearchParams(searchParams)
    if (t === 'workshops') {
      // `view` only applies to the Prompts tab — drop it when leaving.
      params.delete('view')
      params.delete('tab')
    } else {
      params.set('tab', t)
    }
    const qs = params.toString()
    navigate(qs ? `/s/prep?${qs}` : '/s/prep', { replace: true })
  }

  // Roving-tabindex arrow navigation (mirrors the ProfilePage tablist pattern).
  const handleTabKeyDown = (e: React.KeyboardEvent) => {
    const idx = TABS.findIndex(t => t.key === tab)
    let next = -1
    if (e.key === 'ArrowRight') next = (idx + 1) % TABS.length
    else if (e.key === 'ArrowLeft') next = (idx - 1 + TABS.length) % TABS.length
    else if (e.key === 'Home') next = 0
    else if (e.key === 'End') next = TABS.length - 1
    if (next === -1) return
    e.preventDefault()
    switchTab(TABS[next].key)
    const buttons = tablistRef.current?.querySelectorAll<HTMLButtonElement>('[role="tab"]')
    buttons?.[next]?.focus()
  }

  return (
    <div className="flex min-h-0 flex-1 flex-col">
      <div className="flex-shrink-0 border-b border-border bg-card px-6">
        <div ref={tablistRef} role="tablist" aria-label="Prep" className="flex gap-0.5" onKeyDown={handleTabKeyDown}>
          {TABS.map(t => (
            <button
              key={t.key}
              role="tab"
              id={`prep-tab-${t.key}`}
              aria-selected={tab === t.key}
              aria-controls={`prep-panel-${t.key}`}
              tabIndex={tab === t.key ? 0 : -1}
              onClick={() => switchTab(t.key)}
              className={`flex items-center gap-1.5 border-b-2 px-4 py-3 text-sm font-medium transition-colors ${
                tab === t.key
                  ? 'border-secondary text-foreground'
                  : 'border-transparent text-muted-foreground hover:text-foreground'
              }`}
            >
              <t.icon size={15} />
              {t.label}
            </button>
          ))}
        </div>
      </div>

      <div
        role="tabpanel"
        id={`prep-panel-${tab}`}
        aria-labelledby={`prep-tab-${tab}`}
        tabIndex={0}
        className="min-h-0 flex-1 overflow-y-auto focus-visible:outline-none"
      >
        <Suspense fallback={<div className="p-6 text-center text-muted-foreground">Loading...</div>}>
          {tab === 'workshops' && <WorkshopsTab />}
          {tab === 'prompts' && <PromptLibraryTab />}
        </Suspense>
      </div>
    </div>
  )
}
