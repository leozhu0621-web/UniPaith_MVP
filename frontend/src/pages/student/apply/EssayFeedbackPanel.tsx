/**
 * Workshops → Essay feedback (FEEDBACK-ONLY).
 *
 * The student pastes an essay they wrote; the backend returns a rubric +
 * structural issues + missing-element prompts. There is, by design, no
 * "rewrite my essay" path — the response schema mechanically excludes it and
 * a CI test (test_workshop_no_generation_contract.py) enforces it.
 *
 * Ship D — input preservation: the draft (essay + prompt + program selection)
 * persists to localStorage keyed per program and is restored on mount, so
 * navigating away never destroys a half-written essay. Cleared on successful
 * submit.
 */
import { useEffect, useRef, useState } from 'react'
import { useMutation } from '@tanstack/react-query'

import { requestEssayFeedback } from '../../../api/workshops-feedback'
import Badge from '../../../components/ui/Badge'
import Button from '../../../components/ui/Button'
import Card from '../../../components/ui/Card'
import { showToast } from '../../../stores/toast-store'
import type { WorkshopFeedbackRun } from '../../../types'

import AIBadge from '../../../components/ui/AIBadge'
import { RubricScores } from './RubricDots'
import { EmptyHint, ErrorNote, ReadinessCard } from './WorkshopShared'
import WorkshopProgramPicker, {
  type ProgramOption,
  type WorkshopMode,
} from './WorkshopProgramPicker'
import { clearWorkshopDraft, loadLastWorkshopDraft, saveWorkshopDraft } from './workshopDrafts'
import {
  IMPORTANCE_LABEL,
  IMPORTANCE_VARIANT,
  SEVERITY_LABEL,
  SEVERITY_VARIANT,
  readinessSummary,
} from './workshopReadiness'

const DRAFT_PREFIX = 'up-essay-draft'

interface EssayDraft {
  essay: string
  prompt: string
  mode: WorkshopMode
  program: ProgramOption | null
}

/** Save the draft when it holds real text; clear it otherwise (or once submitted). */
function persistEssayDraft(d: EssayDraft, lastSubmitted: string | null): void {
  const programId = d.mode === 'program_specific' ? d.program?.programId ?? null : null
  if (d.essay.trim() && d.essay !== lastSubmitted) {
    saveWorkshopDraft(DRAFT_PREFIX, programId, d)
  } else {
    clearWorkshopDraft(DRAFT_PREFIX, programId)
  }
}

export default function EssayFeedbackPanel() {
  // Restore the last draft synchronously on mount (program selection included).
  const [restored] = useState(() => loadLastWorkshopDraft<Partial<EssayDraft>>(DRAFT_PREFIX))
  const [essay, setEssay] = useState(typeof restored?.essay === 'string' ? restored.essay : '')
  const [prompt, setPrompt] = useState(typeof restored?.prompt === 'string' ? restored.prompt : '')
  const [mode, setMode] = useState<WorkshopMode>(
    restored?.mode === 'program_specific' ? 'program_specific' : 'general',
  )
  const [program, setProgram] = useState<ProgramOption | null>(
    restored?.program && typeof restored.program.programId === 'string' ? restored.program : null,
  )
  const [draftRestored, setDraftRestored] = useState(
    typeof restored?.essay === 'string' && restored.essay.trim().length > 0,
  )
  const [run, setRun] = useState<WorkshopFeedbackRun | null>(null)
  // The program the displayed run was generated for — snapshotted at request
  // time so switching the picker afterwards never relabels a stale run.
  const [runProgram, setRunProgram] = useState<ProgramOption | null>(null)

  // Last successfully submitted essay — once submitted, the stored draft is
  // cleared and not re-saved unless the text changes again.
  const lastSubmittedRef = useRef<string | null>(null)
  const draftRef = useRef<EssayDraft>({ essay, prompt, mode, program })
  draftRef.current = { essay, prompt, mode, program }

  // Debounced persist while typing + flush on unmount.
  useEffect(() => {
    const t = setTimeout(() => persistEssayDraft(draftRef.current, lastSubmittedRef.current), 600)
    return () => clearTimeout(t)
  }, [essay, prompt, mode, program])
  useEffect(() => () => persistEssayDraft(draftRef.current, lastSubmittedRef.current), [])

  const feedbackMut = useMutation({
    mutationFn: (target: ProgramOption | null) =>
      requestEssayFeedback({
        essay_text: essay,
        prompt_text: prompt.trim() || null,
        target_program_id: target?.programId ?? null,
      }),
    onSuccess: (r, target) => {
      setRun(r)
      setRunProgram(target)
      lastSubmittedRef.current = essay
      clearWorkshopDraft(DRAFT_PREFIX, target?.programId ?? null)
      setDraftRestored(false)
      showToast('Feedback ready.', 'success')
    },
    onError: (err: unknown) =>
      showToast((err as Error).message ?? 'Could not get feedback.', 'error'),
  })

  const targetProgram = mode === 'program_specific' ? program : null
  const wordCount = essay.trim().split(/\s+/).filter(Boolean).length
  const tooShort = essay.trim().length < 20
  const readiness = run && runProgram ? readinessSummary(run, runProgram.programName) : null

  return (
    <div className="space-y-4">
      <Card className="space-y-3">
        <WorkshopProgramPicker
          mode={mode}
          onModeChange={setMode}
          program={program}
          onProgramChange={setProgram}
        />

        <div>
          <label className="mb-1 block text-sm font-medium text-foreground">Prompt (optional)</label>
          <input
            className="w-full rounded-md border border-border px-3 py-2 text-sm"
            value={prompt}
            onChange={e => setPrompt(e.target.value)}
            maxLength={4000}
            placeholder="e.g., Tell us about a time you led a team"
          />
        </div>

        <div>
          <div className="mb-1 flex items-center justify-between">
            <label className="block text-sm font-medium text-foreground">
              Your essay <span className="text-error">*</span>
            </label>
            {draftRestored && (
              <span className="text-xs text-muted-foreground">Draft restored</span>
            )}
          </div>
          <textarea
            className="w-full rounded-md border border-border px-3 py-2 text-sm"
            rows={14}
            maxLength={20000}
            value={essay}
            onChange={e => {
              setEssay(e.target.value)
              if (draftRestored) setDraftRestored(false)
            }}
            placeholder="Paste your draft. Minimum 20 characters."
          />
          <div className="mt-1 flex items-center justify-between text-xs text-muted-foreground">
            <span>{wordCount} words</span>
            <span>Feedback only — never a rewrite.</span>
          </div>
        </div>

        <div className="flex justify-end">
          <Button
            variant="secondary"
            onClick={() => feedbackMut.mutate(targetProgram)}
            loading={feedbackMut.isPending}
            disabled={tooShort}
          >
            Get feedback
          </Button>
        </div>
      </Card>

      {!run && !feedbackMut.isPending && !feedbackMut.isError && (
        <EmptyHint>Drop in an essay draft to get structured feedback.</EmptyHint>
      )}

      {feedbackMut.isError && !run && <ErrorNote onRetry={() => feedbackMut.mutate(targetProgram)} />}

      {run && (
        <>
          {readiness && runProgram && (
            <ReadinessCard programName={runProgram.programName} summary={readiness} />
          )}

          <Card>
            <div className="mb-3 flex items-center justify-between">
              <div className="text-eyebrow uppercase text-muted-foreground">Rubric scores</div>
              <AIBadge fallback={run.is_stub} />
            </div>
            <RubricScores scores={run.rubric_scores} />
          </Card>

          {(run.structural_issues?.length ?? 0) > 0 && (
            <Card>
              <div className="mb-2 text-eyebrow uppercase text-muted-foreground">
                Structural issues · {run.structural_issues.length}
              </div>
              <ul className="space-y-2">
                {run.structural_issues.map((iss, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm">
                    <Badge variant={SEVERITY_VARIANT[iss.severity]} size="sm">
                      {SEVERITY_LABEL[iss.severity]}
                    </Badge>
                    <div className="flex-1">
                      <div className="text-foreground">{iss.issue}</div>
                      {iss.location_ref && (
                        <div className="mt-0.5 text-xs text-muted-foreground">{iss.location_ref}</div>
                      )}
                    </div>
                  </li>
                ))}
              </ul>
            </Card>
          )}

          {(run.missing_elements?.length ?? 0) > 0 && (
            <Card>
              <div className="mb-2 text-eyebrow uppercase text-muted-foreground">
                Missing elements · {run.missing_elements.length}
              </div>
              <ul className="space-y-2">
                {run.missing_elements.map((m, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm">
                    <Badge variant={IMPORTANCE_VARIANT[m.importance]} size="sm">
                      {IMPORTANCE_LABEL[m.importance]}
                    </Badge>
                    <span className="flex-1 text-foreground">{m.element}</span>
                  </li>
                ))}
              </ul>
            </Card>
          )}
        </>
      )}
    </div>
  )
}
