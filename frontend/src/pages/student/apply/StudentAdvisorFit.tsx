import { useQuery } from '@tanstack/react-query'
import { Check, Heart, UserCheck } from 'lucide-react'
import { getStudentAdvisorMatches, type StudentAdvisorFit } from '../../../api/graduate'
import Card from '../../../components/ui/Card'
import Badge from '../../../components/ui/Badge'

function FitBar({ score }: { score: number }) {
  const color = score >= 60 ? 'bg-secondary' : score >= 30 ? 'bg-secondary/60' : 'bg-muted-foreground/40'
  return (
    <div className="flex items-center gap-2">
      <div className="h-1.5 w-20 overflow-hidden rounded-full bg-muted">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${Math.max(2, score)}%` }} />
      </div>
      <span className="w-8 text-right text-sm font-semibold tabular-nums text-foreground">
        {Math.round(score)}
      </span>
    </div>
  )
}

function AdvisorRow({ a }: { a: StudentAdvisorFit }) {
  return (
    <div
      className={`rounded-lg border p-3 ${
        a.mutual ? 'border-secondary/40 bg-secondary/5' : 'border-border bg-background'
      }`}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <span className="font-medium text-foreground">{a.faculty_name}</span>
            {a.title && <span className="text-xs text-muted-foreground">{a.title}</span>}
            {a.mutual && (
              <Badge variant="info">
                <Heart size={11} /> Mutual interest
              </Badge>
            )}
            {a.accepting_students && (
              <Badge variant="success">
                <Check size={11} /> Accepting
              </Badge>
            )}
            {a.funding_available && <Badge variant="info">Funding available</Badge>}
          </div>
          {a.shared_interests.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-1">
              {a.shared_interests.map((s, i) => (
                <span key={i} className="rounded bg-muted px-2 py-0.5 text-xs text-muted-foreground">
                  {s}
                </span>
              ))}
            </div>
          )}
        </div>
        <div className="shrink-0">
          <FitBar score={a.alignment_score} />
        </div>
      </div>
    </div>
  )
}

/** Spec 41 §2.1 / §10 — "Advisors who fit your research" (student-facing, read
 * only). Self-gates: renders nothing unless the program is graduate and the
 * department has faculty to rank. */
export default function StudentAdvisorFit({ applicationId }: { applicationId: string }) {
  const { data } = useQuery({
    queryKey: ['student-advisor-fit', applicationId],
    queryFn: () => getStudentAdvisorMatches(applicationId),
  })

  if (!data?.is_graduate || data.matches.length === 0) return null

  return (
    <Card pad={false} className="mb-4 p-5">
      <div className="mb-1 flex items-center gap-2">
        <span className="text-secondary">
          <UserCheck size={16} />
        </span>
        <h3 className="text-sm font-semibold text-foreground">Advisors who fit your research</h3>
      </div>
      <p className="mb-4 text-xs text-muted-foreground">
        Ranked by how closely each advisor's work matches your research interests. Naming an advisor
        in your research intent above — and having them flag interest in you — earns a mutual match.
      </p>
      <div className="space-y-2.5">
        {data.matches.slice(0, 8).map((a, i) => (
          <AdvisorRow key={i} a={a} />
        ))}
      </div>
    </Card>
  )
}
