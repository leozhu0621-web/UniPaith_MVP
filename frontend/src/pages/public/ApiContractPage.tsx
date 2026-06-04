import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Boxes, GitFork, Lock, Network, ShieldCheck, Workflow } from 'lucide-react'

import { getApiContract } from '../../api/build'
import type { RouterGroup } from '../../types/build'
import Card from '../../components/ui/Card'
import usePageTitle from '../../hooks/usePageTitle'
import {
  CardSkeleton,
  Chip,
  ErrorState,
  FilterRow,
  GoalShell,
  Hero,
  SectionHeading,
  Stat,
  StatBand,
  StatSkeleton,
} from './goalUi'

// Spec 50 — the front↔back API contract. The router map is generated from
// GET /api/v1/build/api-contract, which reads the *running* route table — so the
// page is the machine source of truth spec 50 §5 points at and can't drift.

const CONVENTION_ICONS = [Network, Lock, Boxes, GitFork]

const ROLE_TONE: Record<string, 'cobalt' | 'neutral' | 'success'> = {
  student: 'cobalt',
  institution: 'neutral',
  shared: 'neutral',
  public: 'success',
  mixed: 'neutral',
}

function GroupCard({ group }: { group: RouterGroup }) {
  const methods = Object.entries(group.methods)
  return (
    <Card className="flex h-full flex-col gap-2 p-5">
      <div className="flex items-start justify-between gap-2">
        <h3 className="font-mono text-[15px] font-semibold text-foreground">{group.tag}</h3>
        <Chip tone="cobalt">{group.route_count} routes</Chip>
      </div>

      <div className="flex flex-wrap items-center gap-1.5">
        <Chip tone={ROLE_TONE[group.role] ?? 'neutral'}>{group.role}</Chip>
        <Chip tone={group.access === 'public' ? 'success' : 'neutral'} icon={group.access === 'public' ? undefined : Lock}>
          {group.access}
        </Chip>
        <span className="text-[11px] text-muted-foreground">
          {methods.map(([m, n]) => `${m} ${n}`).join(' · ')}
        </span>
      </div>

      <ul className="mt-1 space-y-0.5">
        {group.sample_paths.map(p => (
          <li key={p} className="truncate font-mono text-[11px] text-muted-foreground" title={p}>
            {p}
          </li>
        ))}
      </ul>
    </Card>
  )
}

const ROLE_FILTERS = [
  { key: 'all', label: 'All' },
  { key: 'public', label: 'Public' },
  { key: 'student', label: 'Student' },
  { key: 'institution', label: 'Institution' },
  { key: 'shared', label: 'Shared' },
]

export default function ApiContractPage() {
  usePageTitle('API contract · Spec 50')
  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['build-api-contract'],
    queryFn: getApiContract,
    staleTime: 5 * 60_000,
  })

  const [role, setRole] = useState('all')

  const groups = useMemo(() => {
    const list = data?.groups ?? []
    return list.filter(g => role === 'all' || g.role === role)
  }, [data, role])

  const drift = data
    ? data.summary.route_count - data.summary.doc_claimed_routes
    : 0

  return (
    <GoalShell>
      <Hero
        eyebrow="API contract · Spec 50"
        title="The front↔back handshake, read live from the routes."
        lede="One prefix (/api/v1), bearer auth, three roles, an idiomatic envelope, and one hard invariant: AI endpoints never 5xx — they fall back. The router map below is generated from the running route table, so it shows exactly what's deployed."
      >
        <span className="inline-flex items-center gap-1.5 rounded-pill border border-primary/40 px-3 py-1 text-[13px] font-semibold text-foreground">
          <span className="h-1.5 w-1.5 rounded-full bg-primary" aria-hidden />
          Generated live — can't drift
        </span>
      </Hero>

      <StatBand isError={isError}>
        {isLoading || !data ? (
          [0, 1, 2, 3].map(i => <StatSkeleton key={i} />)
        ) : (
          <>
            <Stat value={data.summary.route_count} label="Live routes under /api/v1" />
            <Stat value={data.summary.router_count} label="Routers (OpenAPI tags)" />
            <Stat value={data.summary.public_route_count} label="Public (no-auth) routes" />
            <Stat value={data.summary.ai_endpoint_count} label="AI endpoints (never 5xx)" />
          </>
        )}
      </StatBand>

      {/* Doc-vs-live correction (spec 50 §5: the running code wins) */}
      {data && (
        <Card variant="card-flush" className="mt-6 flex items-start gap-3 p-4">
          <Workflow size={18} className="mt-0.5 shrink-0 text-secondary" />
          <p className="text-sm text-muted-foreground">
            Spec 50 was drafted at{' '}
            <span className="font-semibold text-foreground">
              {data.summary.doc_claimed_routers} routers / {data.summary.doc_claimed_routes} routes
            </span>{' '}
            (2026-05-30). The live count is{' '}
            <span className="font-semibold text-foreground">
              {data.summary.router_count} / {data.summary.route_count}
            </span>{' '}
            {drift > 0 ? `(+${drift} routes since)` : ''} — specs 39–46 landed after the doc. Per
            spec 50 §5, the running code wins, and this page reads it directly.
          </p>
        </Card>
      )}

      {/* Conventions */}
      <section className="mt-16">
        <SectionHeading
          icon={ShieldCheck}
          title="The cross-cutting contract"
          sub="What every endpoint agrees to, regardless of feature."
        />
        <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {data
            ? data.conventions.map((c, i) => {
                const Icon = CONVENTION_ICONS[i % CONVENTION_ICONS.length]
                return (
                  <Card key={c.title} className="p-5">
                    <Icon size={20} className="text-secondary" />
                    <h3 className="mt-3 text-h3 text-foreground">{c.title}</h3>
                    <p className="mt-1.5 text-sm text-muted-foreground">{c.body}</p>
                  </Card>
                )
              })
            : !isError && [0, 1, 2, 3].map(i => <CardSkeleton key={i} />)}
        </div>
      </section>

      {/* Router map */}
      <section className="mt-16">
        <SectionHeading
          icon={Boxes}
          title="The live router map"
          sub="Grouped by OpenAPI tag. Public/authenticated is a conservative read — the authoritative guard is each route's dependency."
        />
        <div className="mt-6">
          <FilterRow options={ROLE_FILTERS} value={role} onChange={setRole} />
        </div>

        {isError ? (
          <ErrorState onRetry={() => refetch()} label="We couldn't load the API contract just now." />
        ) : (
          <>
            {data && (
              <p className="mt-5 text-sm text-muted-foreground">
                Showing {groups.length} of {data.summary.router_count} routers
              </p>
            )}
            <div className="mt-3 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {data
                ? groups.map(g => <GroupCard key={g.tag} group={g} />)
                : [0, 1, 2, 3, 4, 5].map(i => <CardSkeleton key={i} className="h-32" />)}
            </div>
          </>
        )}
      </section>

      {/* AI invariant + status taxonomy */}
      <section className="mt-16 grid gap-6 lg:grid-cols-2">
        <div>
          <SectionHeading
            icon={GitFork}
            title="AI endpoints never 5xx"
            sub="On timeout, parse error or guardrail trip these fall back to a deterministic path and return 200 with a source indicator."
          />
          <ul className="mt-4 space-y-2">
            {(data?.ai_endpoints ?? []).map(p => (
              <li
                key={p}
                className="truncate rounded-lg border border-border bg-card p-3 font-mono text-[12px] text-muted-foreground"
                title={p}
              >
                {p}
              </li>
            ))}
            {!data && !isError && [0, 1, 2, 3].map(i => <CardSkeleton key={i} className="h-10" />)}
          </ul>
        </div>

        <div>
          <SectionHeading icon={Network} title="Status-code taxonomy" sub="How the client reads each code." />
          <div className="mt-4 overflow-hidden rounded-lg border border-border">
            <table className="w-full text-left text-sm">
              <thead className="bg-muted text-[11px] uppercase tracking-wider text-muted-foreground">
                <tr>
                  <th className="px-3 py-2 font-semibold">Code</th>
                  <th className="px-3 py-2 font-semibold">When</th>
                  <th className="hidden px-3 py-2 font-semibold sm:table-cell">Frontend</th>
                </tr>
              </thead>
              <tbody>
                {(data?.status_taxonomy ?? []).map(s => (
                  <tr key={s.code} className="border-t border-border">
                    <td className="px-3 py-2 font-mono text-[12px] font-semibold text-foreground">
                      {s.code}
                    </td>
                    <td className="px-3 py-2 text-muted-foreground">{s.when}</td>
                    <td className="hidden px-3 py-2 text-muted-foreground sm:table-cell">
                      {s.frontend}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>
    </GoalShell>
  )
}
