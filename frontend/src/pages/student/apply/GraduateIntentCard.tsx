import { useEffect, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { GraduationCap } from 'lucide-react'
import {
  getStudentGraduateIntent,
  putStudentGraduateIntent,
} from '../../../api/graduate'
import Card from '../../../components/ui/Card'
import Button from '../../../components/ui/Button'
import Textarea from '../../../components/ui/Textarea'
import { Toggle } from '../../institution/program-editor/widgets'
import { TagInput } from '../../institution/graduate/GradWidgets'
import { showToast } from '../../../stores/toast-store'

/** Spec 41 §3 — the applicant states research interests + target advisors + a
 * statement of purpose on a graduate application. Self-gates: renders nothing
 * unless the program is graduate. */
export default function GraduateIntentCard({ applicationId }: { applicationId: string }) {
  const qc = useQueryClient()
  const { data } = useQuery({
    queryKey: ['student-grad-intent', applicationId],
    queryFn: () => getStudentGraduateIntent(applicationId),
  })

  const [interests, setInterests] = useState<string[]>([])
  const [advisors, setAdvisors] = useState<string[]>([])
  const [sop, setSop] = useState('')
  const [fundingRequired, setFundingRequired] = useState(true)

  useEffect(() => {
    const intent = data?.intent
    if (intent) {
      setInterests(intent.research_interests ?? [])
      setAdvisors(intent.target_advisor_names ?? [])
      setSop(intent.statement_of_purpose ?? '')
      setFundingRequired(intent.funding_required ?? true)
    }
  }, [data])

  const saveMut = useMutation({
    mutationFn: () =>
      putStudentGraduateIntent(applicationId, {
        research_interests: interests,
        target_advisor_names: advisors,
        statement_of_purpose: sop,
        funding_required: fundingRequired,
      }),
    onSuccess: () => {
      showToast('Research interests saved', 'success')
      qc.invalidateQueries({ queryKey: ['student-grad-intent', applicationId] })
    },
    onError: () => showToast('Could not save', 'error'),
  })

  // Hidden for undergrad programs (§6) and until the gate is known.
  if (!data?.is_graduate) return null

  return (
    <Card pad={false} className="mb-4 p-5">
      <div className="mb-1 flex items-center gap-2">
        <span className="text-secondary">
          <GraduationCap size={16} />
        </span>
        <h3 className="text-sm font-semibold text-foreground">Research &amp; advisors</h3>
      </div>
      <p className="mb-4 text-xs text-muted-foreground">
        Graduate admissions is faculty-driven. Share your research interests and the advisors whose
        work fits yours — the department uses this to surface advisors who fit you.
      </p>
      <div className="space-y-4">
        <TagInput
          label="Research interests"
          values={interests}
          onChange={setInterests}
          placeholder="Add an interest and press Enter"
        />
        <TagInput
          label="Target advisors"
          values={advisors}
          onChange={setAdvisors}
          placeholder="Name an advisor and press Enter"
        />
        <Textarea
          label="Statement of purpose (optional)"
          value={sop}
          onChange={e => setSop(e.target.value)}
          rows={4}
          placeholder="A short statement of your research direction…"
        />
        <div className="flex items-center justify-between">
          <Toggle
            checked={fundingRequired}
            onChange={setFundingRequired}
            label="I require funding to attend"
          />
          <Button
            variant="secondary"
            size="sm"
            loading={saveMut.isPending}
            onClick={() => saveMut.mutate()}
          >
            Save
          </Button>
        </div>
      </div>
    </Card>
  )
}
