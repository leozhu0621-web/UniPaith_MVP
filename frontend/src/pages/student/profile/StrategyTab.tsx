/**
 * Profile → Strategy tab.
 *
 * Read-mostly. Shows the active strategy if one exists; otherwise a CTA to
 * generate one (which requires at least one active academic goal upstream).
 * Editing creates a NEW draft (clone-and-modify) and archives the original
 * — it is NOT auto-activated. The tab surfaces a follow-up "Activate" action
 * on each draft so the user controls promotion explicitly.
 *
 * Phase B: rule-based generator (is_stub=true). Phase C will land the LLM-
 * written narrative; this tab's UI doesn't need to change when that happens.
 */
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { AlertTriangle, CheckCircle2, ChevronRight, Pencil, Sparkles, MessageCircle } from 'lucide-react'

import AIBadge from '../../../components/ui/AIBadge'
import StrategyEditor from './strategy/StrategyEditor'
import ApplicationGamePlan from './strategy/ApplicationGamePlan'
import {
  type UpdateStrategyBody,
  activateStrategy,
  generateStrategy,
  getActiveStrategy,
  listStrategyVersions,
  updateStrategy,
} from '../../../api/strategy'
import Badge from '../../../components/ui/Badge'
import Button from '../../../components/ui/Button'
import Card from '../../../components/ui/Card'
import Modal from '../../../components/ui/Modal'
import { SkeletonCard } from '../../../components/ui/Skeleton'
import { track } from '../../../lib/analytics'
import { showToast } from '../../../stores/toast-store'
import type { StrategyStatus, StudentStrategy } from '../../../types'

const STATUS_VARIANTS: Record<StrategyStatus, 'success' | 'info' | 'neutral'> = {
  active: 'success',
  draft: 'info',
  archived: 'neutral',
}

const STRATEGY_HANDOFF_ROUTE =
  '/s?intent=strategy&source_task=strategy%3Arefine&return_to=%2Fs%2Fprofile%3Ftab%3Dstrategy&artifact_destination=strategy_draft'

type LedgerTone = 'success' | 'warning' | 'neutral'

const LEDGER_TONE_CLASS: Record<LedgerTone, string> = {
  success: 'text-success',
  warning: 'text-warning',
  neutral: 'text-muted-foreground',
}

function validDate(value?: string | null): Date | null {
  if (!value) return null
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? null : date
}

function strategyTimestamp(strategy: StudentStrategy | null): Date | null {
  if (!strategy) return null
  return validDate(strategy.updated_at) ?? validDate(strategy.generated_at) ?? validDate(strategy.created_at)
}

function formatDate(value?: string | null): string | null {
  const date = validDate(value)
  if (!date) return null
  return new Intl.DateTimeFormat('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  }).format(date)
}

function daysSince(date: Date | null): number | null {
  if (!date) return null
  return Math.max(0, Math.floor((Date.now() - date.getTime()) / 86_400_000))
}

function ageLabel(date: Date | null): string {
  const days = daysSince(date)
  if (days == null) return 'No timestamp'
  if (days === 0) return 'Updated today'
  if (days === 1) return 'Updated yesterday'
  return `Updated ${days}d ago`
}

function pathCount(strategy: StudentStrategy | null): number {
  if (!strategy) return 0
  return [
    strategy.academic_path.length > 0,
    strategy.financial_path.length > 0,
    strategy.geographic_path.length > 0,
  ].filter(Boolean).length
}

function anchorCount(strategy: StudentStrategy | null): number {
  if (!strategy) return 0
  return [
    Boolean(strategy.career_target),
    Boolean(strategy.target_degree),
    Boolean(strategy.narrative),
    strategy.academic_path.length > 0,
    strategy.financial_path.length > 0,
    strategy.geographic_path.length > 0,
  ].filter(Boolean).length
}

function missingAnchor(strategy: StudentStrategy | null): string {
  if (!strategy) return 'No active strategy'
  if (!strategy.career_target) return 'Career target missing'
  if (!strategy.target_degree) return 'Degree target missing'
  if (!strategy.narrative) return 'Narrative missing'
  if (strategy.academic_path.length === 0) return 'Academic path missing'
  if (strategy.financial_path.length === 0) return 'Financial path missing'
  if (strategy.geographic_path.length === 0) return 'Geographic path missing'
  return 'All core anchors present'
}

function sourceSummary(strategy: StudentStrategy): string {
  const sessionCount = strategy.generated_from_session_ids.length
  const source = sessionCount === 0
    ? 'student profile record'
    : `${sessionCount} discovery session${sessionCount === 1 ? '' : 's'}`
  const generated = formatDate(strategy.generated_at) ?? formatDate(strategy.created_at)
  return generated ? `Generated from ${source} on ${generated}.` : `Generated from ${source}.`
}

function StrategyLivingHeader({
  active,
  draftCount,
  onDevelop,
  onGenerate,
  onEditActive,
  isGenerating,
}: {
  active: StudentStrategy | null
  draftCount: number
  onDevelop: () => void
  onGenerate: () => void
  onEditActive?: () => void
  isGenerating: boolean
}) {
  const timestamp = strategyTimestamp(active)
  const days = daysSince(timestamp)
  const stale = days != null && days > 45
  const anchors = anchorCount(active)
  const paths = pathCount(active)
  const sourceText = active ? sourceSummary(active) : 'Create a draft before using strategy-driven recommendations.'
  const headline = active?.career_target
    ? `${active.career_target}${active.target_degree ? ` -> ${active.target_degree}` : ''}`
    : 'No active strategy'

  const ledger: { label: string; value: string; detail: string; tone: LedgerTone }[] = [
    {
      label: 'Direction',
      value: active?.career_target && active?.target_degree ? 'Clear' : 'Needs target',
      detail: active?.career_target && active?.target_degree ? 'Career and degree are both set.' : 'Add the career and degree target.',
      tone: active?.career_target && active?.target_degree ? 'success' : 'warning',
    },
    {
      label: 'Evidence depth',
      value: `${anchors}/6 anchors`,
      detail: missingAnchor(active),
      tone: anchors >= 5 ? 'success' : anchors >= 3 ? 'warning' : 'neutral',
    },
    {
      label: 'Freshness',
      value: !active ? 'Not started' : stale ? 'Review freshness' : 'Current',
      detail: active ? ageLabel(timestamp) : 'No active version yet.',
      tone: !active || stale ? 'warning' : 'success',
    },
    {
      label: 'Version control',
      value: draftCount > 0 ? `${draftCount} draft waiting` : active ? 'Active only' : 'No versions',
      detail: draftCount > 0 ? 'Activate the draft that should drive matches.' : 'No inactive draft is waiting.',
      tone: draftCount > 0 ? 'warning' : active ? 'success' : 'neutral',
    },
  ]

  return (
    <section
      role="region"
      aria-label="Strategy living document"
      className="border-y border-border bg-muted/30 px-4 py-4"
    >
      <div className="flex flex-col gap-3 xl:flex-row xl:items-center xl:justify-between">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <p className="text-eyebrow uppercase text-muted-foreground">Living strategy</p>
            {active && <Badge variant="success" size="sm">Active v{active.version}</Badge>}
            {active?.is_stub && <Badge variant="warning" size="sm">Preview</Badge>}
            {draftCount > 0 && <Badge variant="warning" size="sm">Draft waiting</Badge>}
          </div>
          <h2 className="mt-1 text-lg font-semibold text-foreground">{headline}</h2>
          <p className="mt-1 max-w-3xl text-sm text-muted-foreground">
            {sourceText} {paths}/3 path tracks are grounded; use drafts for exploration and activate only the version that should drive recommendations.
          </p>
        </div>
        <div className="flex flex-col gap-2 sm:flex-row">
          <Button size="sm" variant="secondary" onClick={onDevelop}>
            <MessageCircle size={14} />
            Develop with Uni
          </Button>
          {active && onEditActive && (
            <Button size="sm" variant="tertiary" onClick={onEditActive}>
              <Pencil size={14} />
              Refine active
            </Button>
          )}
          <Button size="sm" onClick={onGenerate} loading={isGenerating}>
            <Sparkles size={14} />
            {active ? 'Generate new draft' : 'Generate first draft'}
          </Button>
        </div>
      </div>

      <div className="mt-4 grid gap-2 md:grid-cols-4">
        {ledger.map(item => (
          <div key={item.label} className="rounded-lg border border-border bg-card p-3">
            <p className="text-xs font-medium text-muted-foreground">{item.label}</p>
            <p className={`mt-1 text-sm font-semibold ${LEDGER_TONE_CLASS[item.tone]}`}>{item.value}</p>
            <p className="mt-1 text-xs text-muted-foreground">{item.detail}</p>
          </div>
        ))}
      </div>
    </section>
  )
}

function StrategyCard({
  strategy,
  onActivate,
  onEdit,
  isActivating,
}: {
  strategy: StudentStrategy
  onActivate?: () => void
  onEdit?: () => void
  isActivating?: boolean
}) {
  return (
    <Card pad={false} className="p-5 space-y-3">
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs uppercase tracking-wide text-muted-foreground">
              Version {strategy.version}
            </span>
            <AIBadge />
            <Badge variant={STATUS_VARIANTS[strategy.status]} size="sm">
              {strategy.status}
            </Badge>
            {strategy.is_stub && (
              <Badge variant="warning" size="sm">
                preview
              </Badge>
            )}
          </div>
          {strategy.career_target && (
            <div className="text-base font-medium text-foreground">{strategy.career_target}</div>
          )}
          {strategy.target_degree && (
            <div className="text-sm text-muted-foreground">→ {strategy.target_degree}</div>
          )}
        </div>
        <div className="flex gap-1">
          {onEdit && (
            <Button size="sm" variant="ghost" onClick={onEdit}>
              <Pencil size={14} className="mr-1" />
              Edit
            </Button>
          )}
          {onActivate && (
            <Button size="sm" onClick={onActivate} loading={isActivating}>
              <CheckCircle2 size={14} className="mr-1" />
              Activate
            </Button>
          )}
        </div>
      </div>

      {strategy.narrative && (
        <div className="text-sm text-foreground whitespace-pre-line border-l-2 border-border pl-3">
          {strategy.narrative}
        </div>
      )}

      {strategy.academic_path.length > 0 && (
        <PathSection title="Academic path">
          {strategy.academic_path.map((step, i) => (
            <PathRow key={i}>
              <div className="text-sm font-medium text-foreground">{step.step}</div>
              {step.options.length > 0 && (
                <div className="text-xs text-muted-foreground">
                  Options: {step.options.join(', ')}
                </div>
              )}
              <div className="text-xs text-muted-foreground italic">{step.rationale}</div>
            </PathRow>
          ))}
        </PathSection>
      )}

      {strategy.financial_path.length > 0 && (
        <PathSection title="Financial path">
          {strategy.financial_path.map((item, i) => (
            <PathRow key={i}>
              <div className="text-sm font-medium text-foreground">{item.aid_type}</div>
              <div className="text-xs text-muted-foreground">{item.eligibility}</div>
              {item.estimated_value && (
                <div className="text-xs text-muted-foreground">≈ {item.estimated_value}</div>
              )}
            </PathRow>
          ))}
        </PathSection>
      )}

      {strategy.geographic_path.length > 0 && (
        <PathSection title="Geographic path">
          {strategy.geographic_path.map((item, i) => (
            <PathRow key={i}>
              <div className="text-sm font-medium text-foreground">{item.region}</div>
              <div className="text-xs text-muted-foreground italic">{item.rationale}</div>
              {item.constraints.length > 0 && (
                <div className="text-xs text-muted-foreground">
                  Constraints: {item.constraints.join(', ')}
                </div>
              )}
            </PathRow>
          ))}
        </PathSection>
      )}

      <div className="rounded-lg bg-muted px-3 py-2 text-xs text-muted-foreground">
        Why this appears: {strategy.status} version {strategy.version}. {sourceSummary(strategy)}
      </div>
    </Card>
  )
}

function PathSection({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div>
      <div className="text-xs uppercase tracking-wide text-muted-foreground mb-1">{title}</div>
      <div className="space-y-2">{children}</div>
    </div>
  )
}

function PathRow({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex items-start gap-2">
      <ChevronRight size={14} className="text-muted-foreground mt-0.5 shrink-0" />
      <div className="space-y-0.5">{children}</div>
    </div>
  )
}

export default function StrategyTab() {
  const qc = useQueryClient()
  const navigate = useNavigate()
  const { data: active, isLoading: activeLoading } = useQuery<StudentStrategy | null>({
    queryKey: ['strategy', 'active'],
    queryFn: () => getActiveStrategy(),
  })
  const { data: versions = [], isLoading: versionsLoading } = useQuery<StudentStrategy[]>({
    queryKey: ['strategy', 'versions'],
    queryFn: () => listStrategyVersions(),
  })

  const [editing, setEditing] = useState<StudentStrategy | null>(null)

  const onSettled = () =>
    Promise.all([
      qc.invalidateQueries({ queryKey: ['strategy', 'active'] }),
      qc.invalidateQueries({ queryKey: ['strategy', 'versions'] }),
      qc.invalidateQueries({ queryKey: ['profile'] }), // strategy_active_id summary
    ])

  const generateMut = useMutation({
    mutationFn: () => generateStrategy(),
    onSuccess: () => showToast('Draft strategy generated.', 'success'),
    onError: (err: unknown) =>
      showToast((err as Error).message ?? 'Could not generate strategy.', 'error'),
    onSettled,
  })

  const activateMut = useMutation({
    mutationFn: (id: string) => activateStrategy(id),
    onSuccess: () => showToast('Strategy activated.', 'success'),
    onError: (err: unknown) =>
      showToast((err as Error).message ?? 'Could not activate.', 'error'),
    onSettled,
  })

  const updateMut = useMutation({
    mutationFn: ({ id, body }: { id: string; body: UpdateStrategyBody }) =>
      updateStrategy(id, body),
    onSuccess: () => {
      showToast('New draft created. Activate when ready.', 'success')
      setEditing(null)
    },
    onError: (err: unknown) =>
      showToast((err as Error).message ?? 'Could not update.', 'error'),
    onSettled,
  })

  const drafts = versions.filter(v => v.status === 'draft')
  const archived = versions.filter(v => v.status === 'archived')
  const isLoading = activeLoading || versionsLoading
  const developWithUni = () => {
    track('strategy_refine_clicked', {
      route: STRATEGY_HANDOFF_ROUTE,
      surface: 'profile_strategy',
      active_strategy_id: active?.id ?? null,
    })
    track('uni_chat_handoff_started', {
      intent: 'strategy',
      source_task: 'strategy:refine',
      return_to: '/s/profile?tab=strategy',
      artifact_destination: 'strategy_draft',
      route: STRATEGY_HANDOFF_ROUTE,
    })
    navigate(STRATEGY_HANDOFF_ROUTE)
  }

  return (
    <div className="space-y-6">
      {!isLoading && (
        <StrategyLivingHeader
          active={active ?? null}
          draftCount={drafts.length}
          onDevelop={developWithUni}
          onGenerate={() => generateMut.mutate()}
          onEditActive={active ? () => setEditing(active) : undefined}
          isGenerating={generateMut.isPending}
        />
      )}

      {isLoading && <div className="space-y-3"><SkeletonCard /><SkeletonCard /></div>}

      {/* Spec 03 §7 — on regenerate failure, preserve the existing active
          strategy and surface an inline brand-aligned banner. The toast
          (kept for accessibility) tells the user *something* changed; this
          banner tells them WHAT to expect on the page below it. Surfaces
          even when there is no active strategy yet, so a first-time
          generation failure isn't swallowed. */}
      {generateMut.isError && (
        <div
          role="status"
          className="flex items-start gap-2 rounded-lg border border-border border-l-2 border-l-primary bg-muted px-3 py-2.5 text-sm text-foreground"
        >
          <AlertTriangle size={16} className="mt-0.5 shrink-0 text-warning" aria-hidden="true" />
          <div>
            <div className="font-medium">
              {active
                ? "We couldn't reach the AI service. Showing your last strategy."
                : "We couldn't reach the AI service. No draft was created."}
            </div>
            <div className="text-muted-foreground">Try again in a few moments.</div>
          </div>
        </div>
      )}

      {!isLoading && !active && drafts.length === 0 && versions.length === 0 && (
        <Card pad={false} className="p-5 text-sm text-muted-foreground">
          You don't have a strategy yet. Generate one with AI, develop it with Uni, or write your
          own — generation needs at least one active academic goal (add one in the Goals tab).
        </Card>
      )}

      {/* Application game-plan — the tactical half of the strategy (Ship B §2). */}
      <ApplicationGamePlan />

      {active && (
        <div>
          <div className="text-xs uppercase tracking-wide text-muted-foreground mb-2">
            Active strategy
          </div>
          <StrategyCard strategy={active} onEdit={() => setEditing(active)} />
        </div>
      )}

      {drafts.length > 0 && (
        <div id="strategy-drafts">
          <div className="text-xs uppercase tracking-wide text-muted-foreground mb-2">Drafts</div>
          <div className="space-y-3">
            {drafts.map(d => (
              <StrategyCard
                key={d.id}
                strategy={d}
                onActivate={() => activateMut.mutate(d.id)}
                isActivating={activateMut.isPending && activateMut.variables === d.id}
                onEdit={() => setEditing(d)}
              />
            ))}
          </div>
        </div>
      )}

      {archived.length > 0 && (
        <div>
          <div className="text-xs uppercase tracking-wide text-muted-foreground mb-2">
            Earlier versions
          </div>
          <div className="space-y-3 opacity-70">
            {archived.slice(0, 3).map(a => (
              <StrategyCard key={a.id} strategy={a} />
            ))}
            {archived.length > 3 && (
              <div className="text-xs text-muted-foreground">
                {archived.length - 3} older version(s) hidden.
              </div>
            )}
          </div>
        </div>
      )}

      {editing && (
        <Modal
          isOpen
          onClose={() => setEditing(null)}
          title={`Edit v${editing.version}`}
          size="lg"
        >
          <StrategyEditor
            initial={editing}
            onCancel={() => setEditing(null)}
            onSubmit={body => updateMut.mutate({ id: editing.id, body })}
            submitting={updateMut.isPending}
          />
        </Modal>
      )}
    </div>
  )
}
