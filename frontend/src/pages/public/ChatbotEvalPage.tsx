import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import {
  ArrowRight,
  BookOpenCheck,
  Bot,
  CircleCheck,
  ClipboardCheck,
  Gavel,
  GraduationCap,
  Heart,
  ListChecks,
  MessageSquare,
  Network,
  RefreshCw,
  Ruler,
  ShieldAlert,
  ShieldCheck,
  Sparkles,
} from 'lucide-react'

import { getChatbotEval } from '../../api/build'
import type {
  ChatbotAgent,
  ChatbotBuildTask,
  ChatbotConstitution,
  ChatbotConstitutionDimension,
  ChatbotEvalSuite,
  ChatbotLoopStage,
  ReadinessStatus,
} from '../../types/build'
import Button from '../../components/ui/Button'
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

// Spec 61 — the chatbot training & evaluation loop, read from
// GET /api/v1/build/chatbot-eval. The behavior constitution (the versioned
// rubric), the always-on safety / crisis floor, the deterministic pre-judge
// checks, the chatbot eval adapter, and the golden set + red-team battery — each
// honestly classified live·partial·planned. The constitution dimensions + version
// are parsed from the live rubric files, the case counts are read off disk by the
// runner's loaders, the suites are confirmed against the live runner, and the
// agent tiers + provider come from the registry + settings — so the page can't
// claim a standard the deployed agents aren't held to. Built to the bar it
// documents: skeletons (never a blank flash), motion on the design tokens,
// keyboard-accessible filters, dark-safe semantic tokens.

const THE_BAR =
  'The chatbot is good when a student is met with warmth and grounded, specific guidance — ' +
  'never an invented fact, never a written essay, never a promised admission — and when a ' +
  'moment of real distress is met with empathy and a path to a human. Good is measured, not asserted.'

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

const DIMENSION_ICONS: Record<string, typeof ShieldCheck> = {
  groundedness: BookOpenCheck,
  constitution_adherence: ClipboardCheck,
  helpfulness: Sparkles,
  role_adherence: GraduationCap,
  safety: ShieldAlert,
  brand_voice: MessageSquare,
  tone: Heart,
}

const AGENT_ICONS: Record<string, typeof Bot> = {
  student_advisor: GraduationCap,
  faculty_assistant: Bot,
}

function StatusChip({ status }: { status: ReadinessStatus }) {
  return <Chip tone={STATUS_TONE[status]}>{STATUS_LABEL[status]}</Chip>
}

function HardFloorChip() {
  return (
    <Chip tone="warning" icon={ShieldAlert}>
      Hard floor
    </Chip>
  )
}

function AgentCard({ agent }: { agent: ChatbotAgent }) {
  const Icon = AGENT_ICONS[agent.key] ?? Bot
  const isClaude = agent.provider === 'anthropic'
  return (
    <Card className="flex h-full flex-col gap-3 p-5">
      <div className="flex items-start justify-between gap-3">
        <span className="inline-flex items-center gap-2 text-h3 leading-snug text-foreground">
          <Icon size={18} className="shrink-0 text-secondary" />
          {agent.title}
        </span>
        <Chip tone={isClaude ? 'success' : 'warning'}>{isClaude ? 'Claude' : agent.provider}</Chip>
      </div>
      <div className="flex flex-wrap items-center gap-1.5">
        <Chip tone="neutral">Spec {agent.spec}</Chip>
        <Chip tone="cobalt">{agent.tier}</Chip>
      </div>
      <p className="text-sm text-muted-foreground">{agent.role}</p>
      <p className="text-sm text-foreground">{agent.blurb}</p>
      <p className="mt-auto pt-1 font-mono text-[11px] text-muted-foreground">{agent.file}</p>
    </Card>
  )
}

function DimensionCard({ dimension }: { dimension: ChatbotConstitutionDimension }) {
  const Icon = DIMENSION_ICONS[dimension.key] ?? ClipboardCheck
  return (
    <Card className="flex h-full flex-col gap-2 p-5">
      <div className="flex items-start justify-between gap-3">
        <span className="inline-flex items-center gap-2 text-h3 leading-snug text-foreground">
          <Icon size={18} className="shrink-0 text-secondary" />
          {dimension.label}
        </span>
        {dimension.hard_floor && <HardFloorChip />}
      </div>
      <p className="font-mono text-[11px] text-muted-foreground">{dimension.key}</p>
      <p className="text-sm text-muted-foreground">{dimension.summary}</p>
    </Card>
  )
}

function LoopStageCard({ stage }: { stage: ChatbotLoopStage }) {
  return (
    <Card className="flex h-full flex-col gap-2 p-4">
      <div className="flex items-center justify-between gap-2">
        <span className="inline-flex h-6 w-6 items-center justify-center rounded-full bg-secondary/10 text-[12px] font-semibold text-secondary">
          {stage.n}
        </span>
        <StatusChip status={stage.status} />
      </div>
      <h3 className="text-sm font-semibold text-foreground">{stage.title}</h3>
      <p className="text-[12px] text-muted-foreground">{stage.blurb}</p>
    </Card>
  )
}

function SuiteRow({ suite }: { suite: ChatbotEvalSuite }) {
  return (
    <li className="flex flex-col gap-1 py-3 sm:flex-row sm:items-start sm:gap-3">
      <div className="flex shrink-0 items-center gap-2 sm:w-40">
        <StatusChip status={suite.status} />
        {suite.hard_floor && <HardFloorChip />}
      </div>
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <span className="font-mono text-[13px] text-foreground">{suite.key}</span>
          <Chip tone="neutral">Spec 61 {suite.section}</Chip>
          <Chip tone="cobalt">{suite.case_count} cases</Chip>
        </div>
        <p className="mt-0.5 text-[12px] text-muted-foreground">{suite.blurb}</p>
      </div>
    </li>
  )
}

function TaskRow({ task }: { task: ChatbotBuildTask }) {
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

function ConstitutionMeta({ constitutions }: { constitutions: ChatbotConstitution[] }) {
  const present = constitutions.filter(c => c.present)
  if (present.length === 0) return null
  return (
    <div className="flex flex-wrap items-center gap-2">
      {present.map(c => (
        <Chip key={c.agent} tone="neutral" icon={BookOpenCheck}>
          {c.agent} · v{c.version}
        </Chip>
      ))}
    </div>
  )
}

export default function ChatbotEvalPage() {
  usePageTitle('Chatbot training & evaluation · Spec 61')
  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['build-chatbot-eval'],
    queryFn: getChatbotEval,
    staleTime: 5 * 60_000,
  })

  const [dimFilter, setDimFilter] = useState<string>('all')

  // The student constitution is the primary, highest-stakes rubric.
  const studentConstitution = useMemo(
    () => data?.constitutions.find(c => c.agent === 'student' && c.present),
    [data],
  )
  const dimensions = useMemo(() => {
    const list = studentConstitution?.dimensions ?? []
    if (dimFilter === 'hard_floor') return list.filter(d => d.hard_floor)
    return list
  }, [studentConstitution, dimFilter])

  return (
    <GoalShell>
      <Hero
        eyebrow="Chatbot training & evaluation · Spec 61"
        title="The chatbot, held to a measured standard."
        lede={THE_BAR}
      >
        {data && (
          <span className="inline-flex items-center gap-1.5 rounded-pill border border-primary/40 px-3 py-1 text-[13px] font-semibold text-foreground">
            <span className="h-1.5 w-1.5 rounded-full bg-primary" aria-hidden />
            {data.summary.all_agents_claude ? 'Both agents are Claude' : 'Provider mix'} · verified via{' '}
            <code className="font-mono text-[12px]">ai_turns.provider</code>
          </span>
        )}
        <a
          href="#constitution"
          className="inline-flex items-center gap-1 text-[13px] font-semibold text-secondary hover:underline"
        >
          Jump to the constitution <ArrowRight size={14} />
        </a>
      </Hero>

      {/* Headline stats — read live from the running backend */}
      <StatBand>
        {isLoading || !data ? (
          [0, 1, 2, 3].map(i => <StatSkeleton key={i} />)
        ) : (
          <>
            <Stat
              value={data.summary.dimension_count}
              label="Scored constitution dimensions"
            />
            <Stat
              value={
                <span className="inline-flex items-center gap-1.5">
                  <ClipboardCheck className="text-secondary" size={24} />
                  {data.summary.golden_case_total}
                </span>
              }
              label="Graded eval cases (live from disk)"
            />
            <Stat
              value={
                <span className="inline-flex items-center gap-1.5">
                  <ShieldAlert className="text-secondary" size={22} />
                  {data.summary.hard_floor_suite_count}
                </span>
              }
              label="Hard-floor safety suites"
            />
            <Stat
              value={`${data.summary.suites_live}/${data.summary.suite_count}`}
              label="Eval suites live"
            />
          </>
        )}
      </StatBand>

      {/* The two conversational agents — the provider proof */}
      <section className="mt-16">
        <SectionHeading
          icon={Bot}
          title="Two conversational agents, both Claude"
          sub="The student advisor and the faculty assistant are Claude permanently, by policy (spec 63 — Qwen is never the chatbot). The model tier resolves from the agent registry; the provider is verifiable per call via the ai_turns ledger."
        />
        <div className="mt-6 grid gap-4 sm:grid-cols-2">
          {data
            ? data.agents.map(a => <AgentCard key={a.key} agent={a} />)
            : [0, 1].map(i => <CardSkeleton key={i} className="h-56" />)}
        </div>
      </section>

      {/* §3 — the behavior constitution (the rubric) */}
      <section id="constitution" className="mt-16 scroll-mt-20">
        <SectionHeading
          icon={BookOpenCheck}
          title="The behavior constitution — one source of truth"
          sub="Each dimension is loaded verbatim into the agent's system prompt AND used verbatim as the evaluation rubric — so the standard the agent is steered by can't drift from the standard it's graded against. The versions below are read straight off the rubric files."
        />
        {data && (
          <div className="mt-5">
            <ConstitutionMeta constitutions={data.constitutions} />
          </div>
        )}
        <div className="mt-5">
          <FilterRow
            options={[
              { key: 'all', label: 'All dimensions' },
              { key: 'hard_floor', label: 'Hard floor only' },
            ]}
            value={dimFilter}
            onChange={setDimFilter}
          />
        </div>
        {isError ? (
          <ErrorState onRetry={() => refetch()} label="We couldn't load the chatbot eval surface just now." />
        ) : (
          <div className="mt-5 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {data
              ? dimensions.map(d => <DimensionCard key={d.key} dimension={d} />)
              : [0, 1, 2, 3, 4, 5].map(i => <CardSkeleton key={i} className="h-40" />)}
          </div>
        )}
      </section>

      {/* §6 — the continuous loop */}
      <section className="mt-16">
        <SectionHeading
          icon={RefreshCw}
          title="The continuous improvement loop"
          sub="Production turn → judge → cluster → curate into the golden set → improve a lever → CI-gate → A/B → promote on no-regression. The loop runs on the real ai/evals/ harness; the golden set only grows."
        />
        <div className="mt-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {data
            ? data.loop_stages.map(s => <LoopStageCard key={s.key} stage={s} />)
            : [0, 1, 2, 3, 4, 5, 6, 7].map(i => <CardSkeleton key={i} className="h-28" />)}
        </div>
      </section>

      {/* §7 — eval suites with live case counts */}
      <section className="mt-16">
        <SectionHeading
          icon={Gavel}
          title="Eval suites — gated, not asserted"
          sub="Each suite's case count is read off disk by the runner's own loaders; the safety and red-team suites are deterministic, so they block in CI with no API key — exactly what a hard floor demands."
        />
        <Card className="mt-6 p-2 sm:p-5">
          <ul className="divide-y divide-border">
            {(data?.eval_suites ?? []).map(s => (
              <SuiteRow key={s.key} suite={s} />
            ))}
            {!data &&
              [0, 1, 2, 3].map(i => (
                <li key={i} className="py-3">
                  <div className="h-5 w-3/4 animate-pulse rounded bg-muted" />
                </li>
              ))}
          </ul>
        </Card>
      </section>

      {/* §4/§5 — safety floor + deterministic checks */}
      <section className="mt-16 grid gap-4 lg:grid-cols-2">
        <Card className="flex flex-col gap-3 p-5">
          <h3 className="inline-flex items-center gap-2 text-h3 text-foreground">
            <ShieldAlert size={18} className="text-secondary" />
            Safety & crisis floor
            {data && <StatusChip status={data.safety.status} />}
          </h3>
          <p className="text-sm text-muted-foreground">
            Deterministic and <strong className="text-foreground">always on</strong> — never feature-flag-gated.
            A self-harm / abuse / acute-distress signal is met with empathy and a handoff to a human / crisis
            resource, before the normal turn ever runs.
          </p>
          {data && (
            <div className="space-y-2">
              <p className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
                Crisis signals ({data.safety.crisis_pattern_count})
              </p>
              <div className="flex flex-wrap gap-1.5">
                {data.safety.crisis_subtypes.map(s => (
                  <Chip key={s} tone="warning">
                    {s}
                  </Chip>
                ))}
              </div>
              <p className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
                Harmful asks refused ({data.safety.harmful_pattern_count})
              </p>
              <div className="flex flex-wrap gap-1.5">
                {data.safety.harmful_subtypes.map(s => (
                  <Chip key={s} tone="cobalt">
                    {s}
                  </Chip>
                ))}
              </div>
            </div>
          )}
        </Card>

        <Card className="flex flex-col gap-3 p-5">
          <h3 className="inline-flex items-center gap-2 text-h3 text-foreground">
            <Ruler size={18} className="text-secondary" />
            Deterministic checks — before the judge
          </h3>
          <p className="text-sm text-muted-foreground">
            Cheap, exact, token-free. They catch the failures you never want to pay a judge to notice, and
            they run first — the LLM judge only handles the subjective dimensions.
          </p>
          <ul className="space-y-2">
            {(data?.deterministic_checks ?? []).map(c => (
              <li key={c.name} className="flex gap-2 text-sm text-foreground">
                <CircleCheck size={15} className="mt-0.5 shrink-0 text-success dark:text-success-dark" />
                <span>
                  <code className="font-mono text-[12px] text-secondary">{c.name}</code> — {c.blurb}
                </span>
              </li>
            ))}
            {!data &&
              [0, 1, 2, 3, 4].map(i => (
                <li key={i} className="h-4 w-2/3 animate-pulse rounded bg-muted" />
              ))}
          </ul>
        </Card>
      </section>

      {/* §10 — build-task checklist */}
      <section className="mt-16">
        <SectionHeading
          icon={ListChecks}
          title="Build-task checklist"
          sub="Spec 61 §10 — each task classified by what's shipped versus what's next. The traffic-dependent halves (the production sample→judge cron, A/B promotion, the live 👍/👎 curate job) are named as in-progress, not hidden."
        />
        <Card className="mt-6 p-2 sm:p-5">
          <ul className="divide-y divide-border">
            {(data?.build_tasks ?? []).map(t => (
              <TaskRow key={t.text} task={t} />
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
      <section className="mt-16">
        <SectionHeading
          icon={CircleCheck}
          title="Acceptance"
          sub="Spec 61 §11 — the definition of done, held to the same honest live/in-progress/planned bar."
        />
        <Card className="mt-6 p-2 sm:p-5">
          <ul className="divide-y divide-border">
            {(data?.acceptance ?? []).map(a => (
              <li key={a.text} className="flex items-start gap-3 py-3">
                <StatusChip status={a.status} />
                <span className="text-sm text-foreground">{a.text}</span>
              </li>
            ))}
            {!data &&
              [0, 1, 2].map(i => (
                <li key={i} className="py-3">
                  <div className="h-5 w-2/3 animate-pulse rounded bg-muted" />
                </li>
              ))}
          </ul>
        </Card>
      </section>

      {/* Backing routes — the conversational surfaces this loop governs */}
      <section className="mt-16">
        <SectionHeading
          icon={Network}
          title="Backed by live routes"
          sub="Resolved straight from the running route table — the loop only governs surfaces the deployed app actually serves."
        />
        <div className="mt-6 grid gap-4 lg:grid-cols-2">
          <Card className="flex flex-col gap-3 p-5">
            <h3 className="inline-flex items-center gap-2 text-h3 text-foreground">
              <GraduationCap size={18} className="text-secondary" />
              Student advisor (Discovery)
              {data && <Chip tone="cobalt">{data.routes.discovery.length}</Chip>}
            </h3>
            <ul className="space-y-1.5">
              {(data?.routes.discovery ?? []).map(p => (
                <li key={p} className="flex items-start gap-2 font-mono text-[12px] text-foreground">
                  <CircleCheck size={13} className="mt-0.5 shrink-0 text-success dark:text-success-dark" />
                  <span className="break-all">{p}</span>
                </li>
              ))}
              {!data && [0, 1, 2].map(i => <li key={i} className="h-4 w-2/3 animate-pulse rounded bg-muted" />)}
            </ul>
          </Card>
          <Card className="flex flex-col gap-3 p-5">
            <h3 className="inline-flex items-center gap-2 text-h3 text-foreground">
              <Bot size={18} className="text-secondary" />
              Faculty assistant (Inbox)
              {data && <Chip tone="cobalt">{data.routes.institution_reply.length}</Chip>}
            </h3>
            <ul className="space-y-1.5">
              {(data?.routes.institution_reply ?? []).map(p => (
                <li key={p} className="flex items-start gap-2 font-mono text-[12px] text-foreground">
                  <CircleCheck size={13} className="mt-0.5 shrink-0 text-success dark:text-success-dark" />
                  <span className="break-all">{p}</span>
                </li>
              ))}
              {!data && [0, 1, 2].map(i => <li key={i} className="h-4 w-2/3 animate-pulse rounded bg-muted" />)}
            </ul>
          </Card>
        </div>
      </section>

      {/* §12 — open questions */}
      {data && data.open_questions.length > 0 && (
        <section className="mt-16">
          <SectionHeading
            icon={Sparkles}
            title="Open questions"
            sub="The deliberate calls still open — spec 61 §12."
          />
          <div className="mt-6 grid gap-4 sm:grid-cols-3">
            {data.open_questions.map(q => (
              <Card key={q.q} className="flex h-full flex-col gap-2 p-5">
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
          Steered and graded by the same words.
        </p>
        <p className="mx-auto mt-2 max-w-xl text-muted-foreground">
          The dimensions, case counts and suite statuses above are read straight from the running backend —
          the constitution files, the fixtures on disk, the live runner. The safety floor and red-team
          battery are hard floors; the production sampling and A/B promotion are named as what's next.
        </p>
        <div className="mt-5 flex flex-wrap items-center justify-center gap-3">
          <Link to="/goal">
            <Button size="lg" variant="secondary">
              Back to the build hub
            </Button>
          </Link>
          <Link to="/goal/claude-api">
            <Button size="lg" variant="tertiary">
              See the AI agent fleet
            </Button>
          </Link>
        </div>
      </section>
    </GoalShell>
  )
}
