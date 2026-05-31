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
import { lazy, Suspense, useState } from 'react'
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

  return (
    <div className="mx-auto max-w-4xl p-6">
      <header className="mb-4">
        <h2 className="text-h3 text-student-ink">Workshops</h2>
        <p className="mt-1 text-sm text-student-text">
          Coaching on essays, interviews, and test prep — <strong>feedback-only</strong>. I score,
          flag structural issues, and suggest questions; I won't write your essay or answers for you.
        </p>
      </header>

      {showDisclosure && (
        <div className="mb-4 flex items-start gap-3 rounded-lg border border-cobalt/30 bg-cobalt/5 px-4 py-3">
          <p className="flex-1 text-sm text-student-ink">
            Workshops give you feedback. We never write your essay for you.
          </p>
          <button
            type="button"
            onClick={dismissDisclosure}
            className="shrink-0 rounded p-0.5 text-student-text transition-colors hover:text-student-ink"
            aria-label="Dismiss"
          >
            <X size={16} />
          </button>
        </div>
      )}

      <div className="mb-4 flex gap-1 border-b border-divider">
        {SUB_TABS.map(t => (
          <button
            key={t.key}
            type="button"
            onClick={() => setSub(t.key)}
            className={`flex items-center gap-1.5 border-b-2 px-4 py-2 text-sm font-medium transition-colors ${
              sub === t.key
                ? 'border-student text-student'
                : 'border-transparent text-student-text hover:text-student-ink'
            }`}
          >
            <t.icon size={14} />
            {t.label}
          </button>
        ))}
      </div>

      <Suspense fallback={<div className="py-6 text-sm text-student-text">Loading…</div>}>
        {sub === 'essay' && <EssayFeedbackPanel />}
        {sub === 'interview' && <InterviewPracticePanel />}
        {sub === 'test' && <TestGuidancePanel />}
      </Suspense>
    </div>
  )
}
