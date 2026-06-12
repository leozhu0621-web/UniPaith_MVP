import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import {
  Activity,
  AlertTriangle,
  ArrowRight,
  CircleCheck,
  Clock,
  Cpu,
  EyeOff,
  FileCheck,
  Fingerprint,
  KeyRound,
  ListChecks,
  Lock,
  Network,
  Scale,
  ScrollText,
  Server,
  Settings2,
  ShieldCheck,
  UserCheck,
} from 'lucide-react'

import { getSecurity } from '../../api/build'
import type {
  ReadinessStatus,
  SecurityBuildTask,
  SecurityComplianceItem,
  SecurityConfigKnob,
  SecurityControl,
} from '../../types/build'
import Button from '../../components/ui/Button'
import Card from '../../components/ui/Card'
import usePageTitle from '../../hooks/usePageTitle'
import {
  CardSkeleton,
  CardTitle,
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

// Spec 58 — the security, trust & compliance surface, read from
// GET /api/v1/build/security. Each control (authN/Z · consent · redaction · PII ·
// input-safety · moderation · audit · rate-limit · headers · secrets · compliance
// · incident) is honestly classified live·partial·planned; the auth posture, the
// four consent levers + their gated-agent counts, the redaction-map size, the PII
// registry counts and the live security-header set are introspected from the
// running app, so the page mirrors the deployed controls and can't claim what
// isn't wired. The page is itself built to the bar it documents: skeletons (never
// a blank flash), motion on the design-system tokens, keyboard-accessible filters.

// §1 — the bar. Static spec text so the lede never flashes empty.
const THE_BAR =
  'Security is a property of the running system, not a policy doc: every request is ' +
  'authenticated and owner-checked, every AI/ML call passes a consent gate before it ' +
  'runs, sensitive data is classified and masked, and the controls that aren’t fully ' +
  'built yet are named — not implied.'

const STATUS_TONE: Record<ReadinessStatus, 'success' | 'cobalt' | 'neutral'> = {
  live: 'success',
  partial: 'cobalt',
  planned: 'neutral',
}
const STATUS_LABEL: Record<ReadinessStatus, string> = {
  live: 'Live',
  partial: 'In progress',
  planned: 'Planned',
}
const STATUS_ORDER: ReadinessStatus[] = ['live', 'partial', 'planned']

const CONTROL_ICONS: Record<string, typeof ShieldCheck> = {
  authn: KeyRound,
  authz: UserCheck,
  consent: ShieldCheck,
  redaction: EyeOff,
  pii: Lock,
  input_safety: FileCheck,
  moderation: Scale,
  audit: ScrollText,
  rate_limit: Activity,
  headers: Server,
  secrets: Fingerprint,
  compliance: Scale,
  incident: AlertTriangle,
}

function StatusChip({ status }: { status: ReadinessStatus }) {
  return <Chip tone={STATUS_TONE[status]}>{STATUS_LABEL[status]}</Chip>
}

function ControlCard({ control }: { control: SecurityControl }) {
  const Icon = CONTROL_ICONS[control.key] ?? ShieldCheck
  return (
    <Card pad={false} className="flex h-full flex-col gap-3 p-5">
      <div className="flex items-start justify-between gap-3">
        <CardTitle icon={Icon} className="leading-snug">
          {control.title}
        </CardTitle>
        <StatusChip status={control.status} />
      </div>

      <div className="flex flex-wrap items-center gap-1.5">
        <Chip tone="neutral">Spec 58 {control.section}</Chip>
        <code className="rounded bg-muted px-1.5 py-0.5 font-mono text-[11px] text-muted-foreground">
          {control.module}
        </code>
      </div>
      <p className="text-sm text-muted-foreground">{control.blurb}</p>

      <div className="space-y-1.5">
        <p className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
          Live today
        </p>
        <ul className="space-y-1.5">
          {control.built.map(item => (
            <li key={item} className="flex gap-2 text-sm text-foreground">
              <CircleCheck size={15} className="mt-0.5 shrink-0 text-success dark:text-success-dark" />
              <span>{item}</span>
            </li>
          ))}
        </ul>
      </div>

      {control.planned.length > 0 && (
        <div className="mt-auto space-y-1.5 pt-1">
          <p className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
            Planned
          </p>
          <ul className="space-y-1.5">
            {control.planned.map(item => (
              <li key={item} className="flex gap-2 text-sm text-muted-foreground">
                <Clock size={14} className="mt-0.5 shrink-0" />
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </Card>
  )
}

function KnobValue({ value }: { value: string | number | boolean }) {
  if (typeof value === 'boolean') {
    return <Chip tone={value ? 'success' : 'neutral'}>{value ? 'on' : 'off'}</Chip>
  }
  return <span className="font-mono text-[13px] text-foreground">{String(value)}</span>
}

function ConfigCard({ knobs }: { knobs: SecurityConfigKnob[] }) {
  return (
    <Card pad={false} className="flex h-full flex-col gap-3 p-5">
      <h3 className="text-h3 text-foreground">Live security config</h3>
      <dl className="divide-y divide-border">
        {knobs.map(k => (
          <div key={k.name} className="flex items-center justify-between gap-3 py-1.5">
            <dt className="font-mono text-[12px] text-muted-foreground">{k.name}</dt>
            <dd>
              <KnobValue value={k.value} />
            </dd>
          </div>
        ))}
      </dl>
    </Card>
  )
}

function TaskRow({ task }: { task: SecurityBuildTask }) {
  return (
    <li className="flex flex-col gap-1 py-3 sm:flex-row sm:items-start sm:gap-3">
      <div className="flex shrink-0 items-center gap-2 sm:w-36">
        <StatusChip status={task.status} />
        <span className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
          {task.section}
        </span>
      </div>
      <div>
        <p className="text-sm text-foreground">{task.text}</p>
        <p className="mt-0.5 text-[12px] text-muted-foreground">{task.evidence}</p>
      </div>
    </li>
  )
}

const REGIME_TONE: Record<string, 'cobalt' | 'gold' | 'neutral'> = {
  FERPA: 'cobalt',
  'GDPR/CCPA': 'cobalt',
  Retention: 'neutral',
}

function ComplianceRow({ item }: { item: SecurityComplianceItem }) {
  return (
    <tr>
      <td className="px-5 py-3">
        <Chip tone={REGIME_TONE[item.regime] ?? 'neutral'}>{item.regime}</Chip>
      </td>
      <td className="px-5 py-3 text-foreground">{item.control}</td>
      <td className="px-5 py-3">
        <StatusChip status={item.status} />
      </td>
      <td className="hidden px-5 py-3 font-mono text-[12px] text-muted-foreground sm:table-cell">
        {item.module}
      </td>
    </tr>
  )
}

export default function SecurityTrustPage() {
  usePageTitle('Security, Trust & Compliance · Spec 58')
  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['build-security'],
    queryFn: getSecurity,
    staleTime: 5 * 60_000,
  })

  const [status, setStatus] = useState<string>('all')

  const controls = useMemo(() => {
    const list = data?.controls ?? []
    return status === 'all' ? list : list.filter(c => c.status === status)
  }, [data, status])

  const statusFilters = useMemo(() => {
    const present = new Set((data?.controls ?? []).map(c => c.status))
    const ordered = STATUS_ORDER.filter(s => present.has(s))
    return [{ key: 'all', label: 'All' }, ...ordered.map(s => ({ key: s, label: STATUS_LABEL[s] }))]
  }, [data])

  return (
    <GoalShell>
      <Hero
        eyebrow="Security, Trust & Compliance · Spec 58"
        title="Security you can read off the running system."
        lede={THE_BAR}
      >
        {data && (
          <span className="inline-flex items-center gap-1.5 rounded-pill border border-primary/40 px-3 py-1 text-[13px] font-semibold text-foreground">
            <span className="h-1.5 w-1.5 rounded-full bg-primary" aria-hidden />
            Boot-guarded against the prod auth bypass · {data.summary.consent_agent_count} AI agents
            consent-mapped
          </span>
        )}
        <a
          href="#controls"
          className="inline-flex items-center gap-1 text-[13px] font-semibold text-secondary hover:underline"
        >
          Jump to the controls <ArrowRight size={14} />
        </a>
      </Hero>

      {/* Headline stats — read live from the running app */}
      <StatBand isError={isError}>
        {isLoading || !data ? (
          [0, 1, 2, 3].map(i => <StatSkeleton key={i} />)
        ) : (
          <>
            <Stat
              value={`${data.summary.controls_live}/${data.summary.control_count}`}
              label="Controls fully live"
            />
            <Stat
              value={
                <span className="inline-flex items-center gap-1.5">
                  <Cpu className="text-secondary" size={24} />
                  {data.summary.consent_agent_count}
                </span>
              }
              label="AI agents consent-mapped"
            />
            <Stat
              value={
                <span className="inline-flex items-center gap-1.5">
                  <Lock className="text-secondary" size={22} />
                  {data.summary.pii_field_count}
                </span>
              }
              label="PII fields classified"
            />
            <Stat value={data.summary.security_header_count} label="Security headers / response" />
          </>
        )}
      </StatBand>

      {/* §1–§9 — the controls */}
      <section id="controls" className="mt-16 scroll-mt-20">
        <SectionHeading
          icon={ShieldCheck}
          title="Thirteen controls"
          sub="Each control is honestly classified — live, in progress, or planned. The auth posture, consent levers, redaction map, PII registry and header set behind them are read straight from the running app, so the status is evidence, not a claim."
        />

        <div className="mt-6">
          <FilterRow options={statusFilters} value={status} onChange={setStatus} />
        </div>

        {isError ? (
          <ErrorState
            onRetry={() => refetch()}
            label="We couldn't load the security posture just now."
          />
        ) : (
          <>
            {data && (
              <p className="mt-5 text-sm text-muted-foreground">
                Showing {controls.length} of {data.summary.control_count} controls ·{' '}
                {data.summary.controls_live} live · {data.summary.controls_partial} in progress ·{' '}
                {data.summary.controls_planned} planned
              </p>
            )}
            <div className="mt-3 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {data
                ? controls.map(c => <ControlCard key={c.key} control={c} />)
                : [0, 1, 2, 3, 4, 5].map(i => <CardSkeleton key={i} className="h-72" />)}
            </div>
            {data && controls.length === 0 && (
              <p className="mt-6 text-center text-muted-foreground">No controls match this filter.</p>
            )}
          </>
        )}
      </section>

      {/* Consent enforcement + PII protection — the two deepest live signals */}
      <section className="mt-16">
        <SectionHeading
          icon={ShieldCheck}
          title="Consent & PII, read live"
          sub="The two controls the page reads straight from code: the consent levers every AI call sits behind, and the PII registry that masking and column-encryption target."
        />
        <div className="mt-6 grid gap-4 lg:grid-cols-2">
          {/* Consent */}
          <Card pad={false} className="flex flex-col gap-4 p-6">
            <div className="flex items-center justify-between gap-2">
              <h3 className="inline-flex items-center gap-2 text-h3 text-foreground">
                <ShieldCheck size={18} className="text-secondary" />
                Consent enforcement
              </h3>
              <Chip tone="success">Live · §4</Chip>
            </div>
            <p className="text-sm text-muted-foreground">
              Every AI/ML call resolves the student&rsquo;s mask first; a denied lever
              short-circuits to the rule-based fallback — never a 5xx.
            </p>
            <ul className="space-y-2">
              {(data?.consent.lever_counts ?? []).map(lc => (
                <li
                  key={lc.lever}
                  className="flex items-center justify-between gap-2 border-b border-border pb-2 last:border-0"
                >
                  <span className="inline-flex items-center gap-2 text-sm font-medium capitalize text-foreground">
                    <KeyRound size={14} className="text-secondary" />
                    {lc.lever}
                  </span>
                  <span className="text-[13px] text-muted-foreground">
                    {lc.agent_count} {lc.agent_count === 1 ? 'agent' : 'agents'} gated
                  </span>
                </li>
              ))}
              {!data && [0, 1, 2, 3].map(i => <li key={i} className="h-6 animate-pulse rounded bg-muted" />)}
            </ul>
            {data && (
              <div className="mt-auto flex flex-wrap gap-2 pt-1 text-[12px] text-muted-foreground">
                <Chip tone="neutral">{data.consent.agent_count} agents mapped</Chip>
                <Chip tone="neutral">{data.consent.redaction_map_size} redaction signals</Chip>
              </div>
            )}
          </Card>

          {/* PII */}
          <Card pad={false} className="flex flex-col gap-4 p-6">
            <div className="flex items-center justify-between gap-2">
              <h3 className="inline-flex items-center gap-2 text-h3 text-foreground">
                <Lock size={18} className="text-secondary" />
                PII classification
              </h3>
              <Chip tone="cobalt">In progress · §3</Chip>
            </div>
            <p className="text-sm text-muted-foreground">
              core/pii.py tags sensitive fields by tier; mask() redacts them in logs and AI
              context. The policy-gated + health tiers are the column-encryption target.
            </p>
            <ul className="space-y-2">
              {(data?.pii.classes ?? []).map(c => (
                <li
                  key={c.key}
                  className="flex items-center justify-between gap-2 border-b border-border pb-2 last:border-0"
                >
                  <span className="text-sm text-foreground">
                    {c.label}
                    {c.encryption_target && (
                      <span className="ml-2 inline-flex items-center">
                        <Chip tone="cobalt" icon={Lock}>
                          encrypt
                        </Chip>
                      </span>
                    )}
                  </span>
                  <span className="font-mono text-[13px] text-muted-foreground">{c.count}</span>
                </li>
              ))}
              {!data && [0, 1, 2, 3].map(i => <li key={i} className="h-6 animate-pulse rounded bg-muted" />)}
            </ul>
            {data && (
              <div className="mt-auto flex flex-wrap gap-2 pt-1 text-[12px] text-muted-foreground">
                <Chip tone="neutral">{data.pii.field_count} fields classified</Chip>
                <Chip tone="neutral">
                  {data.pii.encryption_target_count} encryption targets
                </Chip>
              </div>
            )}
          </Card>
        </div>
      </section>

      {/* Operations — config knobs · headers · auth */}
      <section className="mt-16">
        <SectionHeading
          icon={Settings2}
          title="The posture, read live"
          sub="The deployed security config, the headers set on every response, and the auth state — read straight off the running settings and middleware."
        />
        <div className="mt-6 grid gap-4 lg:grid-cols-3">
          {data ? <ConfigCard knobs={data.config_knobs} /> : <CardSkeleton className="h-72" />}

          <Card pad={false} className="flex flex-col gap-3 p-5">
            <h3 className="inline-flex items-center gap-2 text-h3 text-foreground">
              <Server size={18} className="text-secondary" />
              Security headers
            </h3>
            <ul className="space-y-1.5">
              {(data?.headers.names ?? []).map(h => (
                <li key={h} className="flex items-center gap-2 font-mono text-[12px] text-foreground">
                  <CircleCheck size={14} className="shrink-0 text-success dark:text-success-dark" />
                  {h}
                </li>
              ))}
              {!data && [0, 1, 2].map(i => <li key={i} className="h-4 w-2/3 animate-pulse rounded bg-muted" />)}
            </ul>
            {data && <p className="mt-auto text-[12px] text-muted-foreground">{data.headers.note}</p>}
          </Card>

          <Card pad={false} className="flex flex-col gap-3 p-5">
            <h3 className="inline-flex items-center gap-2 text-h3 text-foreground">
              <KeyRound size={18} className="text-secondary" />
              Authentication
            </h3>
            {data ? (
              <dl className="space-y-2 text-sm">
                <div className="flex items-center justify-between gap-2">
                  <dt className="text-muted-foreground">Environment</dt>
                  <dd className="font-mono text-[13px] text-foreground">{data.auth.environment}</dd>
                </div>
                <div className="flex items-center justify-between gap-2">
                  <dt className="text-muted-foreground">Dev bypass</dt>
                  <dd>
                    <Chip tone={data.auth.cognito_bypass ? 'warning' : 'success'}>
                      {data.auth.cognito_bypass ? 'on (dev)' : 'off'}
                    </Chip>
                  </dd>
                </div>
                <div className="flex items-center justify-between gap-2">
                  <dt className="text-muted-foreground">Bypass safe</dt>
                  <dd>
                    <Chip tone={data.auth.bypass_safe ? 'success' : 'warning'}>
                      {data.auth.bypass_safe ? 'guarded' : 'UNSAFE'}
                    </Chip>
                  </dd>
                </div>
                <div className="flex items-center justify-between gap-2">
                  <dt className="text-muted-foreground">Cognito pool</dt>
                  <dd>
                    <Chip tone={data.auth.pool_configured ? 'success' : 'neutral'}>
                      {data.auth.pool_configured ? 'configured' : '(dev)'}
                    </Chip>
                  </dd>
                </div>
                <p className="pt-1 text-[12px] text-muted-foreground">{data.auth.note}</p>
              </dl>
            ) : (
              [0, 1, 2, 3].map(i => <div key={i} className="h-6 animate-pulse rounded bg-muted" />)
            )}
          </Card>
        </div>
      </section>

      {/* Compliance — FERPA / GDPR / retention */}
      <section className="mt-16">
        <SectionHeading
          icon={Scale}
          title="FERPA · GDPR · retention"
          sub="The compliance obligations mapped to the real module that satisfies each — with what's live versus what's the next build."
        />
        <Card pad={false} className="mt-6 overflow-hidden p-0">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-border bg-muted/40">
              <tr className="text-[11px] uppercase tracking-wider text-muted-foreground">
                <th className="px-5 py-3 font-semibold">Regime</th>
                <th className="px-5 py-3 font-semibold">Control</th>
                <th className="px-5 py-3 font-semibold">Status</th>
                <th className="hidden px-5 py-3 font-semibold sm:table-cell">Module</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {(data?.compliance ?? []).map(c => (
                <ComplianceRow key={`${c.regime}-${c.control}`} item={c} />
              ))}
              {!data &&
                [0, 1, 2, 3].map(i => (
                  <tr key={i}>
                    <td className="px-5 py-3" colSpan={4}>
                      <div className="h-4 w-2/3 animate-pulse rounded bg-muted" />
                    </td>
                  </tr>
                ))}
            </tbody>
          </table>
        </Card>
      </section>

      {/* §10 — build-task checklist */}
      <section className="mt-16">
        <SectionHeading
          icon={ListChecks}
          title="Build-task checklist"
          sub="Spec 58 §10 — each task classified by what's shipped versus what's next. The infra-dependent halves (column encryption, AV scan, WAF, moderation, incident runbook) are named as planned, not hidden."
        />
        <Card pad={false} className="mt-6 p-2 sm:p-5">
          <ul className="divide-y divide-border">
            {(data?.build_tasks ?? []).map(t => (
              <TaskRow key={`${t.section}-${t.text}`} task={t} />
            ))}
            {!data &&
              [0, 1, 2, 3, 4].map(i => (
                <li key={i} className="py-3">
                  <div className="h-5 w-3/4 animate-pulse rounded bg-muted" />
                </li>
              ))}
          </ul>
        </Card>
      </section>

      {/* §11 — acceptance */}
      {data && data.acceptance.length > 0 && (
        <section className="mt-16">
          <SectionHeading
            icon={CircleCheck}
            title="Acceptance"
            sub="Spec 58 §11 — the security bar, line by line, with each item honestly marked live or in progress."
          />
          <Card pad={false} className="mt-6 p-2 sm:p-5">
            <ul className="divide-y divide-border">
              {data.acceptance.map(a => (
                <li key={a.text} className="flex items-start gap-3 py-3">
                  <StatusChip status={a.status} />
                  <span className="text-sm text-foreground">{a.text}</span>
                </li>
              ))}
            </ul>
          </Card>
        </section>
      )}

      {/* §12 — open questions */}
      {data && data.open_questions.length > 0 && (
        <section className="mt-16">
          <SectionHeading
            icon={Network}
            title="Open questions"
            sub="The deliberate calls behind the posture — spec 58 §12."
          />
          <div className="mt-6 grid gap-4 sm:grid-cols-3">
            {data.open_questions.map(q => (
              <Card pad={false} key={q.q} className="flex h-full flex-col gap-2 p-5">
                <h3 className="text-h3 text-foreground">{q.q}</h3>
                <p className="text-sm text-muted-foreground">{q.a}</p>
              </Card>
            ))}
          </div>
        </section>
      )}

      {/* Closing — the page practices what it documents */}
      <section className="mt-16 rounded-xl border border-border bg-card p-8 text-center">
        <p className="inline-flex items-center justify-center gap-2 text-h2 text-foreground">
          <ShieldCheck className="text-secondary" size={24} />
          Honest about what&rsquo;s enforced, and what&rsquo;s next.
        </p>
        <p className="mx-auto mt-2 max-w-xl text-muted-foreground">
          The control statuses, consent counts, redaction-map size, PII registry and header set
          above are read straight from the running app — never asserted in a doc. The gaps are
          named, not implied.
        </p>
        <div className="mt-5 flex flex-wrap items-center justify-center gap-3">
          <Link to="/goal">
            <Button size="lg" variant="secondary">
              Back to the build hub
            </Button>
          </Link>
          <Link to="/goal/backend">
            <Button size="lg" variant="tertiary">
              See the backend posture
            </Button>
          </Link>
        </div>
      </section>
    </GoalShell>
  )
}
