import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { ArrowRight, Award } from 'lucide-react'
import { SectionHeader } from '../../../../components/student/density'
import Badge from '../../../../components/ui/Badge'
import { formatCurrency } from '../../../../utils/format'
import { getScholarshipMatches, type ScholarshipMatch } from '../../../../api/students'

function formatType(t: string): string {
  return t.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
}

/** A compact peek at scholarships the student may qualify for (Spec 2026-06-14
 *  backlog → promoted). The full surface is My Space › Applications › Costs &
 *  aid; this teaser deep-links there. Hides when there are no matches. */
export default function ScholarshipsPeek({ className }: { className?: string }) {
  const navigate = useNavigate()
  const { data = [] } = useQuery({
    queryKey: ['scholarship-matches'],
    queryFn: () => getScholarshipMatches(3),
    retry: false,
    staleTime: 5 * 60 * 1000,
  })

  const top = (data as ScholarshipMatch[]).slice(0, 3)
  if (top.length === 0) return null

  return (
    <div className={className}>
      <SectionHeader
        action={
          <button onClick={() => navigate('/s/applications?tab=costs')} className="inline-flex items-center gap-1 text-xs text-secondary hover:underline">
            See all <ArrowRight size={12} />
          </button>
        }
      >
        Scholarships you may qualify for
      </SectionHeader>
      <div className="space-y-2">
        {top.map(s => (
          <button
            key={s.scholarship_id}
            onClick={() => navigate('/s/applications?tab=costs')}
            className="flex w-full items-center gap-3 rounded-lg border border-border bg-card p-3 text-left transition-shadow hover:elev-raised"
          >
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-secondary/10">
              <Award size={15} className="text-secondary" aria-hidden />
            </div>
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-semibold text-foreground">{s.name}</p>
              {s.reasons.length > 0 && <p className="truncate text-xs text-muted-foreground">{s.reasons.join(' · ')}</p>}
            </div>
            {s.scholarship_type && <Badge variant="neutral">{formatType(s.scholarship_type)}</Badge>}
            <span className="shrink-0 text-sm font-semibold text-foreground">{formatCurrency(s.award_estimate)}</span>
          </button>
        ))}
      </div>
    </div>
  )
}
