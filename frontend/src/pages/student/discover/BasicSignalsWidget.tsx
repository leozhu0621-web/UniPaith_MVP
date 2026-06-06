/**
 * Discover → Basic-layer signals rail widget.
 *
 * Shows captured Basic Layer Required Signals (GPA, education level,
 * country/state preference, gender if shared) the moment the extractor
 * persists them onto StudentProfile + AcademicRecord. This is what
 * makes "the system sees me" feel real — the rail used to only show
 * Identity signals, so the student volunteered four facts and the
 * panel stayed empty.
 */
import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { ExternalLink, GraduationCap } from 'lucide-react'

import { getProfile, listAcademics } from '../../../api/students'
import Card from '../../../components/ui/Card'
import QueryError from '../../../components/ui/QueryError'
import Skeleton from '../../../components/ui/Skeleton'

interface Row {
  label: string
  value: string
}

export default function BasicSignalsWidget() {
  const profileQ = useQuery<any>({
    queryKey: ['profile'],
    queryFn: () => getProfile(),
  })
  const academicsQ = useQuery<any[]>({
    queryKey: ['academics'],
    queryFn: () => listAcademics(),
  })
  const profile = profileQ.data
  const academics = academicsQ.data

  if (profileQ.isLoading || academicsQ.isLoading) {
    return (
      <Card className="space-y-3 p-4">
        <Skeleton className="h-4 w-24" />
        <Skeleton className="h-3 w-full" />
        <Skeleton className="h-3 w-3/5" />
      </Card>
    )
  }

  if (profileQ.isError || academicsQ.isError) {
    return (
      <Card className="space-y-2">
        <div className="flex items-center gap-2 text-foreground font-medium text-sm">
          <GraduationCap size={14} className="text-secondary" />
          Basic signals
        </div>
        <QueryError
          variant="inline"
          detail="Couldn't load your basic signals."
          onRetry={() => {
            profileQ.refetch()
            academicsQ.refetch()
          }}
        />
      </Card>
    )
  }

  const current = (academics ?? []).find((a) => a.is_current) ?? academics?.[0]

  const rows: Row[] = []
  if (current?.gpa != null) {
    rows.push({ label: 'GPA', value: String(current.gpa) })
  }
  if (current?.degree_type) {
    rows.push({
      label: 'Stage',
      value: DEGREE_LABEL[current.degree_type] ?? current.degree_type,
    })
  }
  if (profile?.country_of_residence) {
    const region = profile.domicile_state
      ? `${profile.domicile_state}, ${profile.country_of_residence}`
      : profile.country_of_residence
    rows.push({ label: 'Location', value: region })
  }
  if (profile?.gender_identity) {
    rows.push({ label: 'Identity', value: profile.gender_identity })
  }

  if (rows.length === 0) {
    return (
      <Card className="text-sm text-foreground space-y-2">
        <div className="flex items-center gap-2 text-foreground font-medium">
          <GraduationCap size={14} className="text-secondary" />
          Basic signals
        </div>
        <p className="text-muted-foreground">
          As you share GPA, location, and education stage, I'll capture them here.
        </p>
      </Card>
    )
  }

  return (
    <Card className="space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 text-foreground font-medium text-sm">
          <GraduationCap size={14} className="text-secondary" />
          Basic signals
        </div>
        <Link
          to="/s/profile?tab=overview"
          className="text-xs text-secondary inline-flex items-center gap-1 hover:underline"
        >
          Manage <ExternalLink size={11} />
        </Link>
      </div>
      <dl className="space-y-1.5 text-sm">
        {rows.map((r) => (
          <div key={r.label} className="flex justify-between gap-2">
            <dt className="text-foreground/80">{r.label}</dt>
            <dd className="font-medium text-foreground text-right">{r.value}</dd>
          </div>
        ))}
      </dl>
    </Card>
  )
}

const DEGREE_LABEL: Record<string, string> = {
  high_school: 'High school',
  bachelors: 'Undergraduate',
  masters: 'Graduate',
  phd: 'Doctoral',
  certificate: 'Certificate',
}
