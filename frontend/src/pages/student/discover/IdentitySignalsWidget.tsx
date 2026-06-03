/**
 * Discover → Identity signals (rail widget for the Profile track).
 *
 * Read-only summary of the student_identity row. Live-updates as Discovery
 * extracts new core_values / worldview / self_awareness items. Manage-link
 * sends to /s/profile?tab=identity for editing.
 */
import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { ExternalLink, Sparkles } from 'lucide-react'

import { getIdentity } from '../../../api/identity'
import Card from '../../../components/ui/Card'
import type { StudentIdentity } from '../../../types'

export default function IdentitySignalsWidget() {
  const { data: identity, isLoading } = useQuery<StudentIdentity>({
    queryKey: ['identity'],
    queryFn: () => getIdentity(),
  })

  if (isLoading) {
    return <Card className="text-sm text-foreground">Loading…</Card>
  }

  const values = identity?.core_values ?? []
  const beliefs = identity?.worldview ?? []
  const insights = identity?.self_awareness ?? []
  const total = values.length + beliefs.length + insights.length

  if (total === 0) {
    return (
      <Card className="text-sm text-foreground space-y-2">
        <div className="flex items-center gap-2 text-foreground font-medium">
          <Sparkles size={14} className="text-primary" />
          Identity signals
        </div>
        <p className="italic">
          As you talk, I'll extract values, worldview, and self-awareness moments here.
        </p>
      </Card>
    )
  }

  return (
    <Card className="space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 text-foreground font-medium text-sm">
          <Sparkles size={14} className="text-primary" />
          Identity signals
        </div>
        <Link
          to="/s/profile?tab=identity"
          className="text-xs text-primary inline-flex items-center gap-1 hover:underline"
        >
          Manage <ExternalLink size={11} />
        </Link>
      </div>

      <Section title="Values" count={values.length}>
        {values.slice(0, 5).map((v, i) => (
          <Chip key={i}>{v.value}</Chip>
        ))}
        {values.length > 5 && <Chip muted>+{values.length - 5}</Chip>}
      </Section>

      <Section title="Worldview" count={beliefs.length}>
        {beliefs.slice(0, 4).map((w, i) => (
          <Chip key={i}>{w.belief}</Chip>
        ))}
        {beliefs.length > 4 && <Chip muted>+{beliefs.length - 4}</Chip>}
      </Section>

      <Section title="Self-awareness" count={insights.length}>
        {insights.slice(0, 4).map((s, i) => (
          <Chip key={i}>{s.insight}</Chip>
        ))}
        {insights.length > 4 && <Chip muted>+{insights.length - 4}</Chip>}
      </Section>

      {identity?.identity_summary && (
        <div className="text-xs text-foreground border-l-2 border-border pl-2 italic">
          {identity.identity_summary}
        </div>
      )}
    </Card>
  )
}

function Section({
  title,
  count,
  children,
}: {
  title: string
  count: number
  children: React.ReactNode
}) {
  if (count === 0) return null
  return (
    <div>
      <div className="text-[10px] uppercase tracking-wide text-foreground mb-1.5">
        {title} · {count}
      </div>
      <div className="flex flex-wrap gap-1">{children}</div>
    </div>
  )
}

function Chip({ children, muted = false }: { children: React.ReactNode; muted?: boolean }) {
  return (
    <span
      className={
        muted
          ? 'text-[11px] px-2 py-0.5 rounded-full bg-muted text-foreground'
          : 'text-[11px] px-2 py-0.5 rounded-full bg-primary/10 text-foreground'
      }
    >
      {children}
    </span>
  )
}
