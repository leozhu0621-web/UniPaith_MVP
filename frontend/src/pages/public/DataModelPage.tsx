import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  Boxes,
  CircleCheck,
  Clock,
  Database,
  GitFork,
  KeyRound,
  Layers,
  Sparkles,
  Workflow,
} from 'lucide-react'

import { getDataModel } from '../../api/build'
import type { DataModelDomain, DataModelTable } from '../../types/build'
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

// Spec 51 — the persisted data model. The table list and every count come from
// GET /api/v1/build/data-model, which introspects the *running* SQLAlchemy
// metadata — so this map equals the deployed schema and can't drift.

const CONVENTION_ICONS = [KeyRound, Database, Workflow, Layers, GitFork]

function TableRow({ row }: { row: DataModelTable }) {
  const stats = [
    `${row.column_count} cols`,
    row.fk_count > 0 ? `${row.fk_count} fk` : null,
    row.jsonb_count > 0 ? `${row.jsonb_count} jsonb` : null,
  ].filter(Boolean) as string[]
  return (
    <li className="rounded-lg border border-border bg-card p-3">
      <div className="flex flex-wrap items-center gap-2">
        <code className="font-mono text-[13px] font-semibold text-foreground">{row.table}</code>
        <Chip tone="neutral">{row.module}</Chip>
        {row.spec && <Chip tone="cobalt">Spec {row.spec}</Chip>}
        {row.is_vector && (
          <Chip tone="gold" icon={Sparkles}>
            pgvector
          </Chip>
        )}
        <span className="ml-auto font-mono text-[11px] text-muted-foreground">
          {stats.join(' · ')}
        </span>
      </div>
      {row.note && <p className="mt-1.5 text-[13px] text-muted-foreground">{row.note}</p>}
    </li>
  )
}

function DomainSection({ domain }: { domain: DataModelDomain }) {
  return (
    <div>
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h3 className="flex items-center gap-2 text-h3 text-foreground">
          <Boxes size={18} className="text-secondary" />
          {domain.title}
          <span className="text-[12px] font-normal text-muted-foreground">{domain.section}</span>
        </h3>
        <div className="flex items-center gap-1.5">
          <Chip tone="cobalt">{domain.table_count} tables</Chip>
          <Chip tone="neutral">Spec {domain.spec}</Chip>
        </div>
      </div>
      <p className="mt-1.5 max-w-3xl text-sm text-muted-foreground">{domain.blurb}</p>
      <ul className="mt-3 grid gap-2 lg:grid-cols-2">
        {domain.tables.map(t => (
          <TableRow key={t.table} row={t} />
        ))}
      </ul>
    </div>
  )
}

export default function DataModelPage() {
  usePageTitle('Data model · Spec 51')
  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['build-data-model'],
    queryFn: getDataModel,
    staleTime: 5 * 60_000,
  })

  const [domainKey, setDomainKey] = useState('all')

  const domainFilters = useMemo(() => {
    const opts = [{ key: 'all', label: 'All domains' }]
    for (const d of data?.domains ?? []) opts.push({ key: d.key, label: d.title })
    return opts
  }, [data])

  const domains = useMemo(() => {
    const list = data?.domains ?? []
    return list.filter(d => domainKey === 'all' || d.key === domainKey)
  }, [data, domainKey])

  const driftPlus = data ? data.summary.table_count - data.summary.doc_claimed_tables : 0

  return (
    <GoalShell>
      <Hero
        eyebrow="Data model · Spec 51"
        title="The persisted schema, read live from the models."
        lede="One map of every table the app builds against — grouped by domain, with the columns, foreign keys, JSONB and pgvector flags read straight from the running SQLAlchemy metadata. It is the source of truth, so it can't claim a table the deployed schema doesn't have."
      >
        <span className="inline-flex items-center gap-1.5 rounded-pill border border-primary/40 px-3 py-1 text-[13px] font-semibold text-foreground">
          <span className="h-1.5 w-1.5 rounded-full bg-primary" aria-hidden />
          Introspected live — can't drift
        </span>
      </Hero>

      <StatBand isError={isError}>
        {isLoading || !data ? (
          [0, 1, 2, 3].map(i => <StatSkeleton key={i} />)
        ) : (
          <>
            <Stat value={data.summary.table_count} label="Live tables" />
            <Stat value={data.summary.column_count} label="Columns" />
            <Stat value={data.summary.fk_count} label="Foreign keys" />
            <Stat value={data.summary.jsonb_column_count} label="JSONB columns" />
          </>
        )}
      </StatBand>

      {/* Doc-vs-live correction (the running schema is the truth) */}
      {data && (
        <Card pad={false} variant="card-flush" className="mt-6 flex items-start gap-3 p-4">
          <Workflow size={18} className="mt-0.5 shrink-0 text-secondary" />
          <p className="text-sm text-muted-foreground">
            Spec 51 was drafted at{' '}
            <span className="font-semibold text-foreground">
              {data.summary.doc_claimed_tables} tables / {data.summary.doc_claimed_model_files} model
              files
            </span>{' '}
            (2026-05-30). The live schema has{' '}
            <span className="font-semibold text-foreground">
              {data.summary.table_count} tables across {data.summary.module_count} modules
            </span>{' '}
            {driftPlus > 0 ? `(+${driftPlus} since)` : ''} — specs 39–50 and the ML / knowledge
            subsystems landed after the doc. The map below is introspected from the running models,
            so it reads the deployed schema directly.
          </p>
        </Card>
      )}

      {/* Conventions (§9) */}
      <section className="mt-16">
        <SectionHeading
          icon={Database}
          title="The schema, as built"
          sub="Five conventions hold across all of it — and the counts above prove the coverage."
        />
        <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {data
            ? data.conventions.map((c, i) => {
                const Icon = CONVENTION_ICONS[i % CONVENTION_ICONS.length]
                return (
                  <Card pad={false} key={c.title} className="p-5">
                    <Icon size={20} className="text-secondary" />
                    <h3 className="mt-3 text-h3 text-foreground">{c.title}</h3>
                    <p className="mt-1.5 text-sm text-muted-foreground">{c.body}</p>
                  </Card>
                )
              })
            : !isError && [0, 1, 2, 3, 4, 5].map(i => <CardSkeleton key={i} />)}
        </div>
      </section>

      {/* The table map, grouped by domain */}
      <section className="mt-16">
        <SectionHeading
          icon={Boxes}
          title="The table map"
          sub="Grouped into five domains over the live model modules. Every deployed table lands in exactly one."
        />
        <div className="mt-6">
          <FilterRow options={domainFilters} value={domainKey} onChange={setDomainKey} />
        </div>

        {isError ? (
          <ErrorState onRetry={() => refetch()} label="We couldn't load the data model just now." />
        ) : (
          <>
            {data && (
              <p className="mt-5 text-sm text-muted-foreground">
                Showing {domains.reduce((n, d) => n + d.table_count, 0)} of{' '}
                {data.summary.table_count} tables
              </p>
            )}
            <div className="mt-3 flex flex-col gap-10">
              {data
                ? domains.map(d => <DomainSection key={d.key} domain={d} />)
                : [0, 1, 2].map(i => <CardSkeleton key={i} className="h-40" />)}
            </div>
          </>
        )}
      </section>

      {/* §7 already built + §8 planned (with live presence) */}
      <section className="mt-16 grid gap-8 lg:grid-cols-2">
        <div>
          <SectionHeading
            icon={CircleCheck}
            title="Already built — what other specs call 'future'"
            sub="These exist in the model layer now; building the feature = wiring UI to an existing table."
          />
          <ul className="mt-4 space-y-2">
            {(data?.already_built ?? []).map(b => (
              <li key={b.table} className="rounded-lg border border-border bg-card p-3">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="text-[14px] font-semibold text-foreground">{b.capability}</span>
                  <code className="font-mono text-[12px] text-muted-foreground">{b.table}</code>
                  <Chip tone="neutral">Spec {b.spec}</Chip>
                  {b.live && (
                    <span className="ml-auto inline-flex items-center gap-1 text-[11px] font-semibold text-success dark:text-success-dark">
                      <CircleCheck size={14} /> Live
                    </span>
                  )}
                </div>
                <p className="mt-1 text-[13px] text-muted-foreground">{b.note}</p>
              </li>
            ))}
            {!data && !isError && [0, 1, 2, 3].map(i => <CardSkeleton key={i} className="h-16" />)}
          </ul>
        </div>

        <div>
          <SectionHeading
            icon={GitFork}
            title="Planned — and what shipped since the doc"
            sub={
              data
                ? `${data.summary.planned_now_live} of ${data.summary.planned_total} tables the doc listed as 'not built' are now live.`
                : 'The doc’s "not built" list, with each table’s live presence computed.'
            }
          />
          <ul className="mt-4 space-y-2">
            {(data?.planned ?? []).map(p => (
              <li key={p.table} className="rounded-lg border border-border bg-card p-3">
                <div className="flex flex-wrap items-center gap-2">
                  <code className="font-mono text-[13px] font-semibold text-foreground">
                    {p.table}
                  </code>
                  <Chip tone="neutral">Spec {p.spec}</Chip>
                  {p.live ? (
                    <Chip tone="gold" icon={Sparkles}>
                      Now live
                    </Chip>
                  ) : (
                    <span className="ml-auto inline-flex items-center gap-1 text-[11px] font-semibold text-muted-foreground">
                      <Clock size={14} /> Planned
                    </span>
                  )}
                </div>
                <p className="mt-1 text-[13px] text-muted-foreground">{p.note}</p>
                {!p.live && p.covered_by_live && (
                  <p className="mt-1 text-[12px] text-secondary">
                    Capability covered live by <code className="font-mono">{p.covered_by}</code>.
                  </p>
                )}
              </li>
            ))}
            {!data && !isError && [0, 1, 2, 3].map(i => <CardSkeleton key={i} className="h-16" />)}
          </ul>
        </div>
      </section>
    </GoalShell>
  )
}
