/**
 * Apply → Workshops sub-tab.
 *
 * Three feedback-only domains: essay, interview, test. The product spec is
 * explicit — workshops do NOT generate the student's artifact. The backend
 * response schema (WorkshopFeedbackResponse) mechanically excludes any field
 * that could carry a generated essay / answer / draft, and a CI test
 * (test_workshop_no_generation_contract.py) asserts it on every commit.
 *
 * The legacy Essays & Resume workshops still exist under the Profile tab for
 * now; they'll be deleted in Phase E once consumers are migrated.
 */
import { lazy, Suspense, useRef, useState } from 'react'
import { FileText, MessageCircleQuestion, ScrollText, X } from 'lucide-react'

const EssayFeedbackPanel = lazy(() => import('./EssayFeedbackPanel'))
const InterviewPracticePanel = lazy(() => import('./InterviewPracticePanel'))
const TestGuidancePanel = lazy(() => import('./TestGuidancePanel'))

type WorkshopSubTab = 'essay' | 'interview' | 'test'

const SUB_TABS: { key: WorkshopSubTab; label: string; icon: typeof FileText }[] = [
  { key: 'essay', label: 'Essay', icon: FileText },
  { key: 'interview', label: 'Interview', icon: MessageCircleQuestion },
  { key: 'test', label: 'Test prep', icon: ScrollText },
]

const DISCLOSURE_KEY = 'up.workshops.disclosureDismissed'

export default function WorkshopsTab() {
  const [sub, setSub] = useState<WorkshopSubTab>('essay')
  const tablistRef = useRef<HTMLDivElement>(null)
  const [showDisclosure, setShowDisclosure] = useState(() => {
    try {
      return localStorage.getItem(DISCLOSURE_KEY) !== '1'
    } catch {
      return true
    }
  })

  const dismissDisclosure = () => {
    setShowDisclosure(false)
    try {
      localStorage.setItem(DISCLOSURE_KEY, '1')
    } catch {
      /* ignore */
    }
  }

  // Arrow-key / Home / End keyboard navigation on the tablist (ARIA tabs pattern).
  const handleTabKeyDown = (e: React.KeyboardEvent<HTMLButtonElement>, idx: number) => {
    const buttons = tablistRef.current?.querySelectorAll<HTMLButtonElement>('[role="tab"]')
    if (!buttons) return
    let next = -1
    if (e.key === 'ArrowRight') next = (idx + 1) % buttons.length
    else if (e.key === 'ArrowLeft') next = (idx - 1 + buttons.length) % buttons.length
    else if (e.key === 'Home') next = 0
    else if (e.key === 'End') next = buttons.length - 1
    if (next >= 0) {
      e.preventDefault()
      buttons[next].focus()
      setSub(SUB_TABS[next].key)
    }
  }

  return (
    <div className="w-full p-6">
      <header className="mb-4">
        <h2 className="text-h3 text-foreground">Workshops</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          Coaching on essays, interviews, and test prep — <strong>feedback-only</strong>. We score
          your draft, flag structural issues, and surface what&apos;s missing — we never write your
          essay for you.
        </p>
      </header>

      {showDisclosure && (
        <div className="mb-4 flex items-start gap-3 rounded-lg border border-secondary/30 bg-secondary/5 px-4 py-3">
          <p className="flex-1 text-sm text-foreground">
            Workshops give you feedback. We never write your essay for you.
          </p>
          <button
            type="button"
            onClick={dismissDisclosure}
            className="shrink-0 rounded p-0.5 text-foreground transition-colors hover:text-foreground"
            aria-label="Dismiss"
          >
            <X size={16} />
          </button>
        </div>
      )}

      <div
        ref={tablistRef}
        role="tablist"
        aria-label="Workshop domains"
        className="mb-4 flex gap-1 border-b border-border"
      >
        {SUB_TABS.map((t, idx) => (
          <button
            key={t.key}
            id={`workshop-tab-${t.key}`}
            type="button"
            role="tab"
            aria-selected={sub === t.key}
            aria-controls={`workshop-panel-${t.key}`}
            tabIndex={sub === t.key ? 0 : -1}
            onClick={() => setSub(t.key)}
            onKeyDown={e => handleTabKeyDown(e, idx)}
            className={`flex items-center gap-1.5 border-b-2 px-4 py-2 text-sm font-medium transition-colors ${
              sub === t.key
                ? 'border-secondary text-secondary'
                : 'border-transparent text-foreground hover:text-foreground'
            }`}
          >
            <t.icon size={14} />
            {t.label}
          </button>
        ))}
      </div>

      <div
        id={`workshop-panel-${sub}`}
        role="tabpanel"
        aria-labelledby={`workshop-tab-${sub}`}
        tabIndex={0}
        className="focus-visible:outline-none"
      >
        <Suspense fallback={<div className="py-6 text-sm text-foreground">Loading…</div>}>
          {sub === 'essay' && <EssayFeedbackPanel />}
          {sub === 'interview' && <InterviewPracticePanel />}
          {sub === 'test' && <TestGuidancePanel />}
        </Suspense>
      </div>
    </div>
  )
}
