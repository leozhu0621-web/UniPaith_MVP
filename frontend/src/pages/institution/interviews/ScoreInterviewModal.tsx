import { useEffect, useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Sparkles } from 'lucide-react'
import { getInterviewRubrics, scoreInterview, prefillInterviewScore } from '../../../api/interviews-admin'
import type { Interview } from '../../../types'
import Modal from '../../../components/ui/Modal'
import Button from '../../../components/ui/Button'
import Select from '../../../components/ui/Select'
import Textarea from '../../../components/ui/Textarea'
import Skeleton from '../../../components/ui/Skeleton'
import QueryError from '../../../components/ui/QueryError'
import { showToast } from '../../../stores/toast-store'

interface Props {
  isOpen: boolean
  onClose: () => void
  onScored: () => void
  interview: Interview | null
}

const RECOMMENDATIONS = [
  { value: 'recommend', label: 'Recommend' },
  { value: 'neutral', label: 'Neutral' },
  { value: 'not_recommend', label: 'Do not recommend' },
]

export default function ScoreInterviewModal({ isOpen, onClose, onScored, interview }: Props) {
  const [rubricIdx, setRubricIdx] = useState(0)
  const [scores, setScores] = useState<Record<string, number>>({})
  const [criterionNotes, setCriterionNotes] = useState<Record<string, string>>({})
  const [notes, setNotes] = useState('')
  const [recommendation, setRecommendation] = useState('')
  const [transcript, setTranscript] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [prefilling, setPrefilling] = useState(false)

  const programId = interview?.program?.id || null
  const rubricsQ = useQuery({
    queryKey: ['interview-rubrics', programId || 'all'],
    queryFn: () => getInterviewRubrics(programId),
    enabled: isOpen,
  })
  const rubrics = useMemo(() => (Array.isArray(rubricsQ.data) ? rubricsQ.data : []), [rubricsQ.data])
  const rubric = rubrics[rubricIdx]

  // Reset transient state whenever a fresh interview opens.
  useEffect(() => {
    if (isOpen) {
      setRubricIdx(0)
      setScores({})
      setCriterionNotes({})
      setNotes('')
      setRecommendation('')
      setTranscript('')
    }
  }, [isOpen, interview?.id])

  const total = useMemo(
    () => Object.values(scores).reduce((sum, n) => sum + (Number(n) || 0), 0),
    [scores],
  )

  const setCriterion = (key: string, value: string, max: number) => {
    const n = Math.max(0, Math.min(max, Number(value) || 0))
    setScores(prev => ({ ...prev, [key]: n }))
  }

  const handlePrefill = async () => {
    if (!interview) return
    setPrefilling(true)
    try {
      const res = await prefillInterviewScore(interview.id, {
        rubric_id: rubric?.id ?? null,
        transcript_or_notes: transcript || notes,
      })
      if (res.available) {
        setScores(prev => ({ ...prev, ...res.criterion_scores }))
        if (res.overall_note) setNotes(res.overall_note)
        if (res.recommendation) setRecommendation(res.recommendation)
        showToast('AI prefilled the rubric — review and adjust before saving', 'success')
      } else {
        showToast('AI prefill unavailable — score manually', 'info')
      }
    } catch {
      showToast('AI prefill unavailable — score manually', 'info')
    } finally {
      setPrefilling(false)
    }
  }

  const handleSubmit = async () => {
    if (!interview) return
    if (!recommendation) {
      showToast('Pick an overall recommendation', 'warning')
      return
    }
    setSubmitting(true)
    try {
      const rubricNotes = (rubric?.criteria || [])
        .map(c => {
          const n = criterionNotes[c.key]?.trim()
          return n ? `${c.label}: ${n}` : ''
        })
        .filter(Boolean)
      const combinedNotes = [notes.trim(), ...rubricNotes].filter(Boolean).join('\n\n') || null
      await scoreInterview(interview.id, {
        criterion_scores: scores,
        total_weighted_score: total,
        interviewer_notes: combinedNotes,
        recommendation,
        rubric_id: rubric?.id ?? null,
      })
      showToast('Interview scored', 'success')
      onScored()
      onClose()
    } catch {
      showToast('Failed to save score', 'error')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Score interview" size="lg">
      <div className="space-y-4">
        {interview && (
          <p className="text-sm text-muted-foreground">
            {interview.applicant?.name} · {interview.program?.name}
          </p>
        )}

        {rubrics.length > 1 && (
          <Select
            label="Rubric"
            options={rubrics.map((r, i) => ({ value: String(i), label: r.rubric_name }))}
            value={String(rubricIdx)}
            onChange={e => {
              setRubricIdx(Number(e.target.value))
              setScores({})
            }}
          />
        )}

        {/* Optional transcript / notes to ground the AI prefill */}
        <div>
          <div className="flex items-center justify-between mb-1">
            <label className="block text-sm font-medium text-foreground">
              Recording transcript or notes <span className="text-muted-foreground">(optional)</span>
            </label>
            <Button
              variant="ghost"
              size="sm"
              onClick={handlePrefill}
              loading={prefilling}
              className="flex items-center gap-1 text-secondary"
            >
              <Sparkles size={14} /> AI prefill
            </Button>
          </div>
          <Textarea
            value={transcript}
            onChange={e => setTranscript(e.target.value)}
            rows={3}
            placeholder="Paste a transcript or your raw notes to let AI suggest a starting score…"
          />
        </div>

        {/* Per-criterion scoring */}
        <div>
          <label className="block text-sm font-medium text-foreground mb-2">Rubric</label>
          {rubricsQ.isLoading ? (
            <div className="space-y-2">
              {Array.from({ length: 3 }).map((_, i) => (
                <Skeleton key={i} className="h-12" />
              ))}
            </div>
          ) : rubricsQ.isError ? (
            <QueryError
              variant="inline"
              detail="We couldn't load the scoring rubric."
              onRetry={() => rubricsQ.refetch()}
            />
          ) : (
            <div className="space-y-3">
              {(rubric?.criteria || []).map(c => (
                <div key={c.key} className="rounded-md border border-border p-3 space-y-2">
                  <div className="flex items-start gap-3">
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-foreground">{c.label}</p>
                      {c.description && (
                        <p className="text-xs text-muted-foreground">{c.description}</p>
                      )}
                    </div>
                    <div className="flex items-center gap-1 shrink-0">
                      <input
                        type="number"
                        min={0}
                        max={c.max}
                        value={scores[c.key] ?? ''}
                        onChange={e => setCriterion(c.key, e.target.value, c.max)}
                        className="w-16 px-2 py-1.5 text-sm text-right rounded-md border border-border bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-ring"
                      />
                      <span className="text-xs text-muted-foreground">/ {c.max}</span>
                    </div>
                  </div>
                  <input
                    type="text"
                    value={criterionNotes[c.key] ?? ''}
                    onChange={e =>
                      setCriterionNotes(prev => ({ ...prev, [c.key]: e.target.value }))
                    }
                    placeholder="Optional note for this criterion"
                    className="w-full px-2 py-1.5 text-xs rounded-md border border-border bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
                  />
                </div>
              ))}
              <div className="flex items-center justify-between pt-2 border-t border-border">
                <span className="text-sm font-medium text-foreground">Total</span>
                <span className="text-sm font-semibold text-foreground">{total}</span>
              </div>
            </div>
          )}
        </div>

        <Select
          label="Overall recommendation"
          options={RECOMMENDATIONS}
          value={recommendation}
          onChange={e => setRecommendation(e.target.value)}
          placeholder="Select recommendation"
        />

        <Textarea
          label="Notes"
          value={notes}
          onChange={e => setNotes(e.target.value)}
          rows={3}
          placeholder="Summarize your assessment…"
        />

        <div className="flex justify-end gap-2 pt-1">
          <Button variant="tertiary" onClick={onClose}>
            Cancel
          </Button>
          <Button variant="secondary" onClick={handleSubmit} loading={submitting}>
            Submit score
          </Button>
        </div>
      </div>
    </Modal>
  )
}
