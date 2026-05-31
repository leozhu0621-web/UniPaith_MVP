/**
 * Apply → Workshops sub-tab.
 *
 * Three feedback-only domains: essay, interview, test. The product spec
 * is explicit — workshops do NOT generate context. The backend response
 * schema (WorkshopFeedbackResponse) mechanically excludes any field that
 * could carry a generated essay / answer / draft, and a CI test
 * (test_workshop_no_generation_contract.py) asserts it on every commit.
 *
 * The legacy Essays & Resume workshops still exist under the Profile tab
 * for now; they'll be deleted in Phase E once consumers are migrated.
 */
import { lazy, Suspense, useState } from 'react'
import { FileText, MessageCircleQuestion, ScrollText } from 'lucide-react'
import LockedFeature from '../../../components/student/LockedFeature'

const EssayFeedbackPanel = lazy(() => import('./EssayFeedbackPanel'))
const InterviewPracticePanel = lazy(() => import('./InterviewPracticePanel'))
const TestGuidancePanel = lazy(() => import('./TestGuidancePanel'))

type WorkshopSubTab = 'essay' | 'interview' | 'test'

const SUB_TABS: { key: WorkshopSubTab; label: string; icon: typeof FileText }[] = [
  { key: 'essay', label: 'Essay', icon: FileText },
  { key: 'interview', label: 'Interview', icon: MessageCircleQuestion },
  { key: 'test', label: 'Test prep', icon: ScrollText },
]

export default function WorkshopsTab() {
  const [sub, setSub] = useState<WorkshopSubTab>('essay')

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <header className="mb-4">
        <h2 className="text-lg font-semibold text-student-ink">Workshops</h2>
        <p className="text-sm text-student-text mt-1">
          Coaching on essays, interviews, and test prep. <strong>Feedback-only</strong> — I'll
          score, flag structural issues, and suggest questions, but I won't write your essay or
          answers for you.
        </p>
      </header>

      <LockedFeature
        feature="workshops"
        title="Workshops are a Plus feature"
        description="Essay, interview, and test-prep coaching is included with UniPaith Plus and during your free trial."
      >
        <div className="flex gap-1 mb-4 border-b border-divider">
          {SUB_TABS.map(t => (
            <button
              key={t.key}
              onClick={() => setSub(t.key)}
              className={`flex items-center gap-1.5 px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
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

        <Suspense fallback={<div className="text-sm text-student-text py-6">Loading…</div>}>
          {sub === 'essay' && <EssayFeedbackPanel />}
          {sub === 'interview' && <InterviewPracticePanel />}
          {sub === 'test' && <TestGuidancePanel />}
        </Suspense>
      </LockedFeature>
    </div>
  )
}
