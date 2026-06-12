import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import {
  ArrowRight,
  Boxes,
  CircleCheck,
  Cpu,
  Database,
  GitFork,
  Layers,
  Lock,
  ShieldCheck,
  Sparkles,
  UserCheck,
  Workflow,
  Zap,
} from 'lucide-react'

import { getAiAgents } from '../../api/aiAgents'
import type { AiAgent, AgentTier } from '../../types/aiAgents'
import AIBadge from '../../components/ui/AIBadge'
import Button from '../../components/ui/Button'
import Card from '../../components/ui/Card'
import FallbackNote from '../../components/ui/FallbackNote'
import usePageTitle from '../../hooks/usePageTitle'

// Spec 45 — the public "Claude API" transparency surface. Renders the live AI
// agent inventory served by GET /api/v1/ai/agents (ai/catalog.py). On-brand:
// cobalt accents + a single gold beat (the flagship tier), Europa type scale,
// semantic dark-safe tokens, no decorative gradients.

const PRINCIPLE_ICONS = [UserCheck, Sparkles, ShieldCheck, ShieldCheck]

const SURFACE_LABELS: Record<string, string> = {
  student: 'Student',
  institution: 'Institution',
  shared: 'Shared',
}

const MODE_LABELS: Record<string, string> = {
  tool_use: 'Tool-use',
  json: 'JSON mode',
  deterministic: 'Deterministic',
}

// ── small presentational helpers ──────────────────────────────────────────

function Chip({
  children,
  tone = 'neutral',
  icon: Icon,
}: {
  children: React.ReactNode
  tone?: 'neutral' | 'cobalt' | 'gold'
  icon?: typeof Lock
}) {
  const tones: Record<string, string> = {
    neutral: 'bg-muted text-muted-foreground',
    cobalt: 'bg-secondary/10 text-secondary',
    gold: 'border border-primary/40 text-foreground',
  }
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-pill px-2 py-0.5 text-[11px] font-semibold ${tones[tone]}`}
    >
      {tone === 'gold' && <span className="h-1.5 w-1.5 rounded-full bg-primary" aria-hidden />}
      {Icon && <Icon size={11} className="shrink-0" />}
      {children}
    </span>
  )
}

function tierTone(tier: string): 'neutral' | 'cobalt' | 'gold' {
  if (tier === 'flagship') return 'gold'
  if (tier === 'workhorse') return 'cobalt'
  return 'neutral'
}

function Stat({ value, label }: { value: React.ReactNode; label: string }) {
  return (
    <div>
      <div className="text-h1 leading-none text-foreground">{value}</div>
      <div className="mt-1.5 text-sm text-muted-foreground">{label}</div>
    </div>
  )
}

function AgentCard({ agent }: { agent: AiAgent }) {
  return (
    <Card pad={false} className="flex h-full flex-col gap-3 p-5">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
            {SURFACE_LABELS[agent.surface] ?? agent.surface} · {agent.group}
            {agent.spec_sections.length > 0 && (
              <span className="text-secondary"> · {agent.spec_sections.join(' ')}</span>
            )}
          </p>
          <h3 className="mt-0.5 text-h3 text-foreground">{agent.title}</h3>
        </div>
        <AIBadge label="Claude" fallback={!agent.enabled} className="shrink-0" />
      </div>

      <p className="text-sm text-muted-foreground">{agent.purpose}</p>

      <div className="mt-auto flex flex-wrap gap-1.5 pt-1">
        <Chip tone={tierTone(agent.tier)} icon={Cpu}>
          {agent.tier_label ?? agent.tier}
          {agent.model_id ? ` · ${agent.model_id}` : ''}
        </Chip>
        <Chip tone={agent.consent ? 'cobalt' : 'neutral'} icon={agent.consent ? Lock : undefined}>
          {agent.consent_label}
        </Chip>
        <Chip>{MODE_LABELS[agent.mode] ?? agent.mode}</Chip>
        {agent.streaming && (
          <Chip icon={Zap} tone="cobalt">
            Streaming
          </Chip>
        )}
      </div>

      <FallbackNote className="not-italic">
        <span className="text-muted-foreground">
          <span className="font-semibold">Falls back to:</span> {agent.fallback}
        </span>
      </FallbackNote>
    </Card>
  )
}

function TierCard({ tier }: { tier: AgentTier }) {
  const isFlagship = tier.tier === 'flagship'
  return (
    <Card pad={false} variant={isFlagship ? 'card-accent' : 'card'} className="flex flex-col gap-2 p-5">
      <div className="flex items-center justify-between">
        <h3 className="inline-flex items-center gap-2 text-h3 text-foreground">
          {isFlagship ? (
            <Sparkles size={18} className="text-primary" />
          ) : (
            <Cpu size={18} className="text-secondary" />
          )}
          {tier.label}
        </h3>
        <Chip tone={tierTone(tier.tier)}>{tier.agent_count} agents</Chip>
      </div>
      {tier.model_id && (
        <code className="font-mono text-xs text-muted-foreground">{tier.model_id}</code>
      )}
      <p className="text-sm text-muted-foreground">{tier.role}</p>
      {tier.price && (
        <p className="mt-auto pt-1 text-[11px] text-muted-foreground">
          ${tier.price.input.toFixed(2)} in · ${tier.price.output.toFixed(2)} out / M tokens
        </p>
      )}
    </Card>
  )
}

// ── filters ───────────────────────────────────────────────────────────────

const SURFACE_FILTERS = [
  { key: 'all', label: 'All' },
  { key: 'student', label: 'Student' },
  { key: 'institution', label: 'Institution' },
  { key: 'shared', label: 'Shared' },
]
const TIER_FILTERS = [
  { key: 'all', label: 'All tiers' },
  { key: 'flagship', label: 'Opus' },
  { key: 'workhorse', label: 'Sonnet' },
  { key: 'batch', label: 'Haiku' },
  { key: 'rule_based', label: 'Rule-based' },
]

function FilterRow({
  options,
  value,
  onChange,
}: {
  options: { key: string; label: string }[]
  value: string
  onChange: (k: string) => void
}) {
  return (
    <div className="flex flex-wrap gap-2">
      {options.map(o => {
        const active = o.key === value
        return (
          <button
            key={o.key}
            type="button"
            onClick={() => onChange(o.key)}
            aria-pressed={active}
            className={
              'rounded-pill px-3 py-1 text-[13px] font-semibold transition-colors ' +
              (active
                ? 'bg-secondary text-secondary-foreground'
                : 'border border-border bg-card text-muted-foreground hover:bg-muted')
            }
          >
            {o.label}
          </button>
        )
      })}
    </div>
  )
}

// ── loading skeleton ────────────────────────────────────────────────────────

function CardSkeleton() {
  return <div className="h-44 rounded-lg border border-border bg-card animate-pulse" />
}

// ── page ────────────────────────────────────────────────────────────────────

export default function ClaudeApiGoalPage() {
  usePageTitle('Claude API · AI Agents')
  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['ai-agents-catalog'],
    queryFn: getAiAgents,
    staleTime: 5 * 60_000,
  })

  const [surface, setSurface] = useState('all')
  const [tier, setTier] = useState('all')

  const agents = useMemo(() => {
    const list = data?.agents ?? []
    return list.filter(
      a => (surface === 'all' || a.surface === surface) && (tier === 'all' || a.tier === tier),
    )
  }, [data, surface, tier])

  const claudeTiers = data?.tiers.filter(t => t.model_id).length ?? 3

  return (
    <div className="mx-auto max-w-6xl px-4 py-12 sm:px-6 sm:py-16 animate-page-in">
      {/* ── Hero ── */}
      <header className="max-w-3xl">
        <p className="text-eyebrow font-semibold uppercase tracking-[0.22em] text-secondary">
          The Claude API migration · Spec 45
        </p>
        <h1 className="mt-3 text-h1 text-foreground sm:text-display">
          Every assistive feature, powered by Claude.
        </h1>
        <p className="mt-5 text-lg text-muted-foreground">
          UniPaith runs one consistent agent contract across the whole product — discovery,
          matching, strategy, workshops, review and more. Each agent names a model tier, sits behind
          a consent lever, validates its own output, and always has a deterministic fallback. This is
          the live inventory, read straight from the running registry.
        </p>
        <div className="mt-6 flex flex-wrap items-center gap-3">
          <span className="inline-flex items-center gap-1.5 rounded-pill border border-primary/40 px-3 py-1 text-[13px] font-semibold text-foreground">
            <span className="h-1.5 w-1.5 rounded-full bg-primary" aria-hidden />
            100% rule-based fallback coverage
          </span>
          <a
            href="#inventory"
            className="inline-flex items-center gap-1 text-[13px] font-semibold text-secondary hover:underline"
          >
            Jump to the agent inventory <ArrowRight size={14} />
          </a>
        </div>
      </header>

      {/* ── Live stats ── */}
      <section className="mt-10 grid grid-cols-2 gap-6 rounded-xl border border-border bg-card p-6 sm:grid-cols-4 sm:p-8">
        {isLoading || !data ? (
          [0, 1, 2, 3].map(i => <div key={i} className="h-16 rounded-lg bg-muted animate-pulse" />)
        ) : (
          <>
            <Stat value={data.summary.agent_count} label="AI agents in production" />
            <Stat value={claudeTiers} label="Claude model tiers" />
            <Stat value={data.summary.llm_agent_count} label="LLM-backed agents" />
            <Stat
              value={
                <span className="inline-flex items-center gap-1.5">
                  <CircleCheck className="text-success" size={28} />
                  {data.summary.fallback_coverage}
                </span>
              }
              label="Never returns a 5xx"
            />
          </>
        )}
      </section>

      {/* ── Principles ── */}
      <section className="mt-16">
        <h2 className="text-h2 text-foreground">How we hold the line</h2>
        <p className="mt-2 max-w-2xl text-muted-foreground">
          Four commitments shape every agent. They are enforced in code, not just stated.
        </p>
        <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {(data?.principles ?? []).map((p, i) => {
            const Icon = PRINCIPLE_ICONS[i] ?? ShieldCheck
            return (
              <Card pad={false} key={p.title} className="p-5">
                <Icon size={20} className="text-secondary" />
                <h3 className="mt-3 text-h3 text-foreground">{p.title}</h3>
                <p className="mt-1.5 text-sm text-muted-foreground">{p.body}</p>
              </Card>
            )
          })}
          {isLoading && !data && [0, 1, 2, 3].map(i => <CardSkeleton key={i} />)}
        </div>
      </section>

      {/* ── Model tiers ── */}
      <section className="mt-16">
        <div className="flex items-center gap-2">
          <Layers className="text-secondary" size={20} />
          <h2 className="text-h2 text-foreground">Three Claude tiers</h2>
        </div>
        <p className="mt-2 max-w-2xl text-muted-foreground">
          Each agent runs at the cheapest tier that does the job well. The flagship tier is reserved
          for the highest-stakes single shots.
        </p>
        <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {data
            ? data.tiers.map(t => <TierCard key={t.tier} tier={t} />)
            : [0, 1, 2, 3].map(i => <CardSkeleton key={i} />)}
        </div>
      </section>

      {/* ── Agent inventory ── */}
      <section id="inventory" className="mt-16 scroll-mt-20">
        <div className="flex items-center gap-2">
          <Boxes className="text-secondary" size={20} />
          <h2 className="text-h2 text-foreground">The agent inventory</h2>
        </div>
        <p className="mt-2 max-w-2xl text-muted-foreground">
          The full fleet, grouped by where it runs. Each agent shows its model tier, the consent
          lever it sits behind, its output mode, and the deterministic path it falls back to.
        </p>

        <div className="mt-6 flex flex-col gap-3">
          <FilterRow options={SURFACE_FILTERS} value={surface} onChange={setSurface} />
          <FilterRow options={TIER_FILTERS} value={tier} onChange={setTier} />
        </div>

        {isError ? (
          <Card pad={false} className="mt-6 p-8 text-center">
            <p className="text-foreground">We couldn't load the agent catalog just now.</p>
            <Button variant="secondary" className="mt-4" onClick={() => refetch()}>
              Retry
            </Button>
          </Card>
        ) : (
          <>
            {data && (
              <p className="mt-5 text-sm text-muted-foreground">
                Showing {agents.length} of {data.summary.agent_count} agents
              </p>
            )}
            <div className="mt-3 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {data
                ? agents.map(a => <AgentCard key={a.name} agent={a} />)
                : [0, 1, 2, 3, 4, 5].map(i => <CardSkeleton key={i} />)}
            </div>
            {data && agents.length === 0 && (
              <p className="mt-6 text-center text-muted-foreground">
                No agents match this filter.
              </p>
            )}
          </>
        )}
      </section>

      {/* ── How it stays safe (validation + fallback flow) ── */}
      <section className="mt-16 grid gap-6 lg:grid-cols-2">
        <div>
          <div className="flex items-center gap-2">
            <ShieldCheck className="text-secondary" size={20} />
            <h2 className="text-h2 text-foreground">Validated output</h2>
          </div>
          <p className="mt-2 text-muted-foreground">{data?.validation.summary}</p>
          <ol className="mt-4 space-y-2">
            {(data?.validation.steps ?? []).map((s, i) => (
              <li key={i} className="flex gap-3 rounded-lg border border-border bg-card p-3">
                <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-secondary/10 text-[13px] font-semibold text-secondary">
                  {i + 1}
                </span>
                <span className="text-sm text-muted-foreground">{s}</span>
              </li>
            ))}
          </ol>
        </div>

        <div>
          <div className="flex items-center gap-2">
            <GitFork className="text-secondary" size={20} />
            <h2 className="text-h2 text-foreground">The fallback flow</h2>
          </div>
          <p className="mt-2 text-muted-foreground">
            Whatever goes wrong, the caller still gets a usable answer.
          </p>
          <ul className="mt-4 space-y-2">
            {(data?.fallback_flow ?? []).map((f, i) => (
              <li key={i} className="rounded-lg border border-border bg-card p-3">
                <p className="text-sm font-semibold text-foreground">{f.trigger}</p>
                <p className="mt-0.5 flex items-start gap-1.5 text-sm text-muted-foreground">
                  <ArrowRight size={14} className="mt-0.5 shrink-0 text-secondary" />
                  {f.action}
                </p>
              </li>
            ))}
          </ul>
        </div>
      </section>

      {/* ── Cache strategy ── */}
      <section className="mt-16">
        <div className="flex items-center gap-2">
          <Database className="text-secondary" size={20} />
          <h2 className="text-h2 text-foreground">Prompt caching, by breakpoint</h2>
        </div>
        <p className="mt-2 max-w-2xl text-muted-foreground">
          Stable instructions are cached so repeat calls stay fast and cheap; the volatile per-call
          tail is always read fresh.
        </p>
        <div className="mt-6 grid gap-4 sm:grid-cols-3">
          {(
            data?.cache_strategy ?? [
              { layer: 'System block', ttl: '1 hour', note: '' },
              { layer: 'Persona block', ttl: '5 minutes', note: '' },
              { layer: 'Per-turn tail', ttl: 'Uncached', note: '' },
            ]
          ).map(c => (
            <Card pad={false} key={c.layer} className="p-5">
              <div className="flex items-center justify-between">
                <h3 className="text-h3 text-foreground">{c.layer}</h3>
                <Chip tone={c.ttl === 'Uncached' ? 'neutral' : 'cobalt'} icon={Workflow}>
                  {c.ttl}
                </Chip>
              </div>
              <p className="mt-2 text-sm text-muted-foreground">{c.note}</p>
            </Card>
          ))}
        </div>
      </section>

      {/* ── Closing CTA ── */}
      <section className="mt-16 rounded-xl border border-border bg-card p-8 text-center">
        <p className="text-h2 text-foreground">Assistive, explainable, yours.</p>
        <p className="mx-auto mt-2 max-w-xl text-muted-foreground">
          AI drafts and suggests across UniPaith — people decide. See how it shows up in the product.
        </p>
        <div className="mt-5 flex flex-wrap items-center justify-center gap-3">
          <Link to="/signup">
            <Button size="lg">Get started</Button>
          </Link>
          <a href="https://unipaith.co" target="_blank" rel="noreferrer">
            <Button size="lg" variant="tertiary">
              How we use AI
            </Button>
          </a>
        </div>
      </section>
    </div>
  )
}
