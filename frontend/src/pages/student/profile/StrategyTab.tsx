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
import { AlertTriangle, CheckCircle2, ChevronDown, ChevronRight, Pencil, Sparkles, MessageCircle } from 'lucide-react'

import AIBadge from '../../../components/ui/AIBadge'
import StrategyEditor from './strategy/StrategyEditor'
import ApplicationGamePlan from './strategy/ApplicationGamePlan'
import PlanOverview from './strategy/PlanOverview'
import SchoolList from './strategy/SchoolList'
import { createSession } from '../../../api/chatSessions'
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
import { showToast } from '../../../stores/toast-store'
import type { StrategyStatus, StudentStrategy } from '../../../types'

const STATUS_VARIANTS: Record<StrategyStatus, 'success' | 'info' | 'neutral'> = {
  active: 'success',
  draft: 'info',
  archived: 'neutral',
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

      <PathDetails strategy={strategy} />
    </Card>
  )
}

/** The academic / financial / geographic paths — the supporting detail of a
 *  strategy. Rendered inline on drafts/archived; tucked into a collapsible on
 *  the lead "Your angle" card so the angle stays the headline. */
function PathDetails({ strategy }: { strategy: StudentStrategy }) {
  return (
    <>
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
    </>
  )
}

/** Lead presentation of the ACTIVE strategy — "Your angle". Leads with the
 *  career → degree headline + the narrative; demotes the three paths to a
 *  collapsible "Plan details" so the angle is what the student reads first. */
function AngleCard({ strategy, onEdit }: { strategy: StudentStrategy; onEdit: () => void }) {
  const [showPaths, setShowPaths] = useState(false)
  const hasPaths =
    strategy.academic_path.length > 0 ||
    strategy.financial_path.length > 0 ||
    strategy.geographic_path.length > 0

  return (
    <Card pad={false} className="p-5 space-y-3">
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs uppercase tracking-wide text-muted-foreground">
              Your angle
            </span>
            <AIBadge />
            {strategy.is_stub && (
              <Badge variant="warning" size="sm">
                preview
              </Badge>
            )}
          </div>
          {strategy.career_target && (
            <div className="text-lg font-medium text-foreground">{strategy.career_target}</div>
          )}
          {strategy.target_degree && (
            <div className="text-sm text-muted-foreground">→ {strategy.target_degree}</div>
          )}
        </div>
        <Button size="sm" variant="ghost" onClick={onEdit}>
          <Pencil size={14} className="mr-1" />
          Edit
        </Button>
      </div>

      {strategy.narrative && (
        <div className="text-sm text-foreground whitespace-pre-line border-l-2 border-border pl-3">
          {strategy.narrative}
        </div>
      )}

      {hasPaths && (
        <div className="border-t border-border pt-3">
          <button
            type="button"
            onClick={() => setShowPaths(v => !v)}
            aria-expanded={showPaths}
            className="flex items-center gap-1 text-xs font-medium text-muted-foreground hover:text-foreground transition-colors"
          >
            {showPaths ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
            Plan details — academic, financial, geographic
          </button>
          {showPaths && (
            <div className="mt-3 space-y-3">
              <PathDetails strategy={strategy} />
            </div>
          )}
        </div>
      )}
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

  // "Develop with Uni" — open the real Sharpen-your-strategy chat template.
  // Creates a template-origin session, then deep-links the chat tab to it
  // (?session=<id>) so it opens straight into the guided TemplateRunner. On any
  // failure we still drop the student into the chat tab so the action never dead-ends.
  const developMut = useMutation({
    mutationFn: () =>
      createSession({
        title: 'Sharpen your strategy',
        topic_key: 'strategy',
        origin_kind: 'template',
        origin_ref: 'sharpen_strategy',
      }),
    onSuccess: session =>
      navigate(`/s?session=${session.id}`, {
        state: { originKind: 'template', originRef: 'sharpen_strategy' },
      }),
    onError: (err: unknown) => {
      showToast((err as Error).message ?? 'Could not open Uni.', 'error')
      navigate('/s')
    },
  })

  const drafts = versions.filter(v => v.status === 'draft')
  const archived = versions.filter(v => v.status === 'archived')
  const isLoading = activeLoading || versionsLoading

  return (
    <div className="space-y-6">
      {/* "Your plan" — connected Planning overview (Spec 2026-06-18). The
          existing strategy detail below is unchanged. */}
      <PlanOverview />

      <div className="flex items-start justify-end">
        <div className="flex shrink-0 items-center gap-2">
          {/* Develop the strategy with Uni — opens the real "Sharpen your
              strategy" chat template (createSession → deep-link the chat tab),
              not a bare intent. */}
          <Button
            variant="secondary"
            onClick={() => developMut.mutate()}
            loading={developMut.isPending}
          >
            <MessageCircle size={14} className="mr-1" />
            Develop with Uni
          </Button>
          <Button onClick={() => generateMut.mutate()} loading={generateMut.isPending}>
            <Sparkles size={14} className="mr-1" />
            Generate new draft
          </Button>
        </div>
      </div>

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
          No strategy yet. Generation needs at least one active academic goal.
        </Card>
      )}

      {/* Application game-plan — the tactical half of the strategy (Ship B §2). */}
      <ApplicationGamePlan />

      {active && (
        <div className="space-y-4">
          {/* Lead with the angle (career → degree + narrative); paths demoted
              to a collapsible inside the card. */}
          <AngleCard strategy={active} onEdit={() => setEditing(active)} />
          {/* The school list — the second half of the white-paper strategy:
              a balanced lineup with separate fit + odds reads. */}
          <SchoolList />
        </div>
      )}

      {drafts.length > 0 && (
        <div>
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
