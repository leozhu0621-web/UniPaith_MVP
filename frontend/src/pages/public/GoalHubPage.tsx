import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import {
  ArrowRight,
  Bell,
  Bot,
  CircleCheck,
  Cpu,
  Database,
  FlaskConical,
  Gauge,
  Layers,
  ListChecks,
  Map as MapIcon,
  Network,
  Rocket,
  Search,
  Server,
  ShieldCheck,
  Sparkles,
  Telescope,
} from 'lucide-react'

import { getBuildOverview } from '../../api/build'
import { qk } from '../../api/queryKeys'
import type { OverviewSurface } from '../../types/build'
import Button from '../../components/ui/Button'
import Card from '../../components/ui/Card'
import usePageTitle from '../../hooks/usePageTitle'
import { GoalShell, Hero, SectionHeading, Stat, StatBand, StatSkeleton } from './goalUi'

// Specs 48–53 — the /goal transparency hub. One landing that links the public
// build surfaces (AI agents · roadmap · feature coverage · API contract · data
// model · acceptance · experience) and shows the live headline numbers, read
// from GET /api/v1/build/overview.

const SURFACE_ICONS: Record<string, typeof MapIcon> = {
  'claude-api': Sparkles,
  roadmap: MapIcon,
  features: ListChecks,
  api: Network,
  'data-model': Database,
  acceptance: Rocket,
  experience: Gauge,
  frontend: Layers,
  backend: Server,
  search: Search,
  knowledge: Telescope,
  realtime: Bell,
  'chatbot-eval': Bot,
  'eval-harness': FlaskConical,
  security: ShieldCheck,
}

const PRINCIPLES: { title: string; body: string; icon: typeof ShieldCheck }[] = [
  {
    title: 'Read from the running system',
    body: "The API map is generated from the live route table; agent tiers and consent levers resolve from the registry. These pages can't claim what the code doesn't have.",
    icon: Network,
  },
  {
    title: 'Nothing silently dropped',
    body: 'Every feature on the founder’s list is mapped — covered, written, or net-new — and classified core, extend or defer. The cuts are explicit.',
    icon: ListChecks,
  },
  {
    title: 'Assistive, never autonomous',
    body: 'AI drafts and suggests across the product; people decide. Every agent falls back to a deterministic path, so a caller never sees a 5xx.',
    icon: ShieldCheck,
  },
]

function SurfaceCard({ surface }: { surface: OverviewSurface }) {
  const Icon = SURFACE_ICONS[surface.key] ?? Network
  return (
    <Link to={surface.path} className="group block h-full">
      <Card interactive className="flex h-full flex-col gap-3 p-6">
        <div className="flex items-start justify-between gap-3">
          <span className="inline-flex items-center gap-2 text-h3 text-foreground">
            <Icon size={20} className="text-secondary" />
            {surface.title}
          </span>
          <span className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
            Spec {surface.spec}
          </span>
        </div>
        <p className="text-sm text-muted-foreground">{surface.blurb}</p>
        <div className="mt-auto flex items-end justify-between pt-2">
          <div>
            <div className="text-h2 leading-none text-foreground">{surface.stat}</div>
            <div className="mt-1 text-[11px] uppercase tracking-wider text-muted-foreground">
              {surface.stat_label}
            </div>
          </div>
          <span className="inline-flex items-center gap-1 text-[13px] font-semibold text-secondary group-hover:underline">
            Explore <ArrowRight size={14} />
          </span>
        </div>
      </Card>
    </Link>
  )
}

export default function GoalHubPage() {
  usePageTitle('How UniPaith is built')
  const { data, isLoading } = useQuery({
    queryKey: qk.buildOverview(),
    queryFn: getBuildOverview,
    staleTime: 5 * 60_000,
  })

  const mvpComplete = Boolean(data?.roadmap.mvp_complete && data?.features.mvp_complete)

  return (
    <GoalShell>
      <Hero
        eyebrow="Build transparency · Specs 45 · 48–58 · 60 · 61 · 62"
        title="How UniPaith is built — in the open."
        lede="The roadmap, the feature coverage map, the API contract, the data model, the acceptance runbook, the experience standards, the frontend engineering spec, the AI agent fleet, the backend production posture, the discovery substrate, live realtime notifications, the security & trust controls, the world-side knowledge engine and how the chatbot is trained and evaluated — surfaced as live, self-verifying pages. Where a page shows a number, it's read straight from the running system, not asserted in a doc."
      >
        {mvpComplete && (
          <span className="inline-flex items-center gap-1.5 rounded-pill border border-primary/40 px-3 py-1 text-[13px] font-semibold text-foreground">
            <span className="h-1.5 w-1.5 rounded-full bg-primary" aria-hidden />
            MVP scope complete
          </span>
        )}
        <a
          href="#surfaces"
          className="inline-flex items-center gap-1 text-[13px] font-semibold text-secondary hover:underline"
        >
          Jump to the surfaces <ArrowRight size={14} />
        </a>
      </Hero>

      {/* Live headline stats */}
      <StatBand>
        {isLoading || !data ? (
          [0, 1, 2, 3].map(i => <StatSkeleton key={i} />)
        ) : (
          <>
            <Stat
              value={`${data.roadmap.shipped}/${data.roadmap.phase_count}`}
              label="Roadmap phases shipped"
            />
            <Stat
              value={`${data.features.mvp_delivered}/${data.features.mvp_scope_count}`}
              label="MVP features delivered"
            />
            <Stat value={data.api.route_count} label="Live API routes" />
            <Stat
              value={
                <span className="inline-flex items-center gap-1.5">
                  <Cpu className="text-secondary" size={26} />
                  {data.agents.agent_count}
                </span>
              }
              label="AI agents in production"
            />
          </>
        )}
      </StatBand>

      {/* Surface cards */}
      <section id="surfaces" className="mt-16 scroll-mt-20">
        <SectionHeading
          icon={MapIcon}
          title="Fifteen ways to read the build"
          sub="Each surface is a public page backed by a live endpoint. Open one to see the detail."
        />
        <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {data
            ? data.surfaces.map(s => <SurfaceCard key={s.key} surface={s} />)
            : [0, 1, 2, 3, 4, 5].map(i => (
                <div key={i} className="h-48 rounded-lg border border-border bg-card animate-pulse" />
              ))}
        </div>
      </section>

      {/* How we build */}
      <section className="mt-16">
        <SectionHeading
          icon={ShieldCheck}
          title="How we hold the line"
          sub="Three commitments shape the whole surface — and the product behind it."
        />
        <div className="mt-6 grid gap-4 sm:grid-cols-3">
          {PRINCIPLES.map(p => (
            <Card key={p.title} className="p-5">
              <p.icon size={20} className="text-secondary" />
              <h3 className="mt-3 text-h3 text-foreground">{p.title}</h3>
              <p className="mt-1.5 text-sm text-muted-foreground">{p.body}</p>
            </Card>
          ))}
        </div>
      </section>

      {/* Closing CTA */}
      <section className="mt-16 rounded-xl border border-border bg-card p-8 text-center">
        <p className="inline-flex items-center justify-center gap-2 text-h2 text-foreground">
          <CircleCheck className="text-success dark:text-success-dark" size={24} />
          Two-sided, assistive, and built to spec.
        </p>
        <p className="mx-auto mt-2 max-w-xl text-muted-foreground">
          Students find programs; institutions find applicants. See how the product shows up.
        </p>
        <div className="mt-5 flex flex-wrap items-center justify-center gap-3">
          <Link to="/signup">
            <Button size="lg">Get started</Button>
          </Link>
          <Link to="/about">
            <Button size="lg" variant="tertiary">
              About UniPaith
            </Button>
          </Link>
        </div>
      </section>
    </GoalShell>
  )
}
