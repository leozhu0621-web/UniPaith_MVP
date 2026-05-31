/**
 * Profile → Experience tab (spec 10 §7).
 * Activities · Work & Service · Competitions · Portfolio · Online Presence.
 */
import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Award, Briefcase, ExternalLink, FolderOpen, Globe, Users } from 'lucide-react'

import {
  createActivity,
  createCompetition,
  createOnlinePresence,
  createPortfolioItem,
  createWorkExperience,
  deleteActivity,
  deleteCompetition,
  deleteOnlinePresence,
  deletePortfolioItem,
  deleteWorkExperience,
  listCompetitions,
  listWorkExperiences,
  updateActivity,
  updateCompetition,
  updateOnlinePresence,
  updatePortfolioItem,
  updateWorkExperience,
} from '../../../api/students'
import Modal from '../../../components/ui/Modal'
import { SkeletonCard } from '../../../components/ui/Skeleton'
import { showToast } from '../../../stores/toast-store'
import { ACTIVITY_TYPES, PLATFORM_TYPES, PORTFOLIO_ITEM_TYPES } from '../../../utils/constants'
import { formatDate } from '../../../utils/format'
import {
  ActivityForm,
  CompetitionForm,
  OnlinePresenceForm,
  PortfolioItemForm,
  WorkExperienceForm,
} from '../components/ProfileForms'
import { EmptyHint, ItemRow, SectionCard, useProfile } from './_shared'

const lastUpdated = (xs: any[] = []) => {
  const ds = xs.map(x => x?.updated_at).filter(Boolean).sort()
  return ds.length ? ds[ds.length - 1] : null
}

type Kind = 'activity' | 'work' | 'competition' | 'portfolio' | 'online'
type Editing = { kind: Kind; item: any } | null

export default function ExperienceTab() {
  const qc = useQueryClient()
  const { data: p, isLoading } = useProfile()
  const { data: work } = useQuery<any[]>({ queryKey: ['work-experiences'], queryFn: listWorkExperiences })
  const { data: comps } = useQuery<any[]>({ queryKey: ['competitions'], queryFn: listCompetitions })
  const [editing, setEditing] = useState<Editing>(null)
  const close = () => setEditing(null)
  const done = (msg: string, keys: string[]) => {
    keys.forEach(k => qc.invalidateQueries({ queryKey: [k] }))
    qc.invalidateQueries({ queryKey: ['profile-overview'] })
    close()
    showToast(msg, 'success')
  }
  const fail = () => showToast("Something didn't work. Try again.", 'error')

  const actCreate = useMutation({ mutationFn: createActivity, onSuccess: () => done('Saved', ['profile']), onError: fail })
  const actUpdate = useMutation({ mutationFn: ({ id, data }: any) => updateActivity(id, data), onSuccess: () => done('Saved', ['profile']), onError: fail })
  const actDelete = useMutation({ mutationFn: deleteActivity, onSuccess: () => done('Deleted', ['profile']), onError: fail })
  const workCreate = useMutation({ mutationFn: createWorkExperience, onSuccess: () => done('Saved', ['profile', 'work-experiences']), onError: fail })
  const workUpdate = useMutation({ mutationFn: ({ id, data }: any) => updateWorkExperience(id, data), onSuccess: () => done('Saved', ['profile', 'work-experiences']), onError: fail })
  const workDelete = useMutation({ mutationFn: deleteWorkExperience, onSuccess: () => done('Deleted', ['profile', 'work-experiences']), onError: fail })
  const compCreate = useMutation({ mutationFn: createCompetition, onSuccess: () => done('Saved', ['profile', 'competitions']), onError: fail })
  const compUpdate = useMutation({ mutationFn: ({ id, data }: any) => updateCompetition(id, data), onSuccess: () => done('Saved', ['profile', 'competitions']), onError: fail })
  const compDelete = useMutation({ mutationFn: deleteCompetition, onSuccess: () => done('Deleted', ['profile', 'competitions']), onError: fail })
  const pfCreate = useMutation({ mutationFn: createPortfolioItem, onSuccess: () => done('Saved', ['profile']), onError: fail })
  const pfUpdate = useMutation({ mutationFn: ({ id, data }: any) => updatePortfolioItem(id, data), onSuccess: () => done('Saved', ['profile']), onError: fail })
  const pfDelete = useMutation({ mutationFn: deletePortfolioItem, onSuccess: () => done('Deleted', ['profile']), onError: fail })
  const opCreate = useMutation({ mutationFn: createOnlinePresence, onSuccess: () => done('Saved', ['profile']), onError: fail })
  const opUpdate = useMutation({ mutationFn: ({ id, data }: any) => updateOnlinePresence(id, data), onSuccess: () => done('Saved', ['profile']), onError: fail })
  const opDelete = useMutation({ mutationFn: deleteOnlinePresence, onSuccess: () => done('Deleted', ['profile']), onError: fail })

  if (isLoading) return <div className="space-y-4"><SkeletonCard /><SkeletonCard /></div>

  const activities = p?.activities ?? []
  const portfolio = p?.portfolio_items ?? []
  const online = p?.online_presence ?? []
  const workList = Array.isArray(work) ? work : []
  const compList = Array.isArray(comps) ? comps : []

  return (
    <div className="space-y-6">
      <SectionCard title="Activities" icon={Users} count={activities.length} lastUpdated={lastUpdated(activities)} onAdd={() => setEditing({ kind: 'activity', item: null })}>
        {activities.length === 0 ? (
          <EmptyHint>No activities yet. Add your first to surface relevant programs.</EmptyHint>
        ) : (
          <div className="space-y-3">
            {activities.map((act: any) => (
              <ItemRow key={act.id} onEdit={() => setEditing({ kind: 'activity', item: act })} onDelete={() => actDelete.mutate(act.id)}>
                <p className="font-medium text-sm text-charcoal">{act.title}{act.organization ? ` — ${act.organization}` : ''}</p>
                <p className="text-xs text-slate">{ACTIVITY_TYPES.find((t: any) => t.value === act.activity_type)?.label || act.activity_type}{act.hours_per_week ? ` · ${act.hours_per_week} hrs/wk` : ''}</p>
              </ItemRow>
            ))}
          </div>
        )}
      </SectionCard>

      <SectionCard title="Work & Service" icon={Briefcase} count={workList.length} lastUpdated={lastUpdated(workList)} onAdd={() => setEditing({ kind: 'work', item: null })}>
        {workList.length === 0 ? (
          <EmptyHint>No work, internships, or volunteering yet.</EmptyHint>
        ) : (
          <div className="space-y-3">
            {workList.map((w: any) => (
              <ItemRow key={w.id} onEdit={() => setEditing({ kind: 'work', item: w })} onDelete={() => workDelete.mutate(w.id)}>
                <p className="font-medium text-sm text-charcoal">{w.role_title} at {w.organization}</p>
                <p className="text-xs text-slate">{w.experience_type}{w.is_current ? ' · Current' : ''}{w.start_date ? ` · ${formatDate(w.start_date)}` : ''}</p>
                {w.description && <p className="text-xs text-slate mt-1 line-clamp-2">{w.description}</p>}
              </ItemRow>
            ))}
          </div>
        )}
      </SectionCard>

      <SectionCard title="Competitions" icon={Award} count={compList.length} lastUpdated={lastUpdated(compList)} onAdd={() => setEditing({ kind: 'competition', item: null })}>
        {compList.length === 0 ? (
          <EmptyHint>No competitions, hackathons, or olympiads yet.</EmptyHint>
        ) : (
          <div className="space-y-3">
            {compList.map((c: any) => (
              <ItemRow key={c.id} onEdit={() => setEditing({ kind: 'competition', item: c })} onDelete={() => compDelete.mutate(c.id)}>
                <p className="font-medium text-sm text-charcoal">{c.competition_name}</p>
                <p className="text-xs text-slate">{c.level}{c.result_placement ? ` · ${c.result_placement}` : ''}{c.year ? ` · ${c.year}` : ''}{c.domain ? ` · ${c.domain}` : ''}</p>
              </ItemRow>
            ))}
          </div>
        )}
      </SectionCard>

      <SectionCard title="Portfolio" icon={FolderOpen} count={portfolio.length} lastUpdated={lastUpdated(portfolio)} onAdd={() => setEditing({ kind: 'portfolio', item: null })}>
        {portfolio.length === 0 ? (
          <EmptyHint>Showcase a project or work sample.</EmptyHint>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {portfolio.map((item: any) => (
              <div key={item.id} className="border border-divider rounded-lg p-3">
                <ItemRow onEdit={() => setEditing({ kind: 'portfolio', item })} onDelete={() => pfDelete.mutate(item.id)}>
                  <p className="font-medium text-sm text-charcoal">{item.title}</p>
                  <p className="text-xs text-slate">{PORTFOLIO_ITEM_TYPES.find((t: any) => t.value === item.item_type)?.label || item.item_type}</p>
                  {item.url && <a href={item.url} target="_blank" rel="noopener noreferrer" className="text-xs text-cobalt story-link">Open</a>}
                </ItemRow>
              </div>
            ))}
          </div>
        )}
      </SectionCard>

      <SectionCard title="Online Presence" icon={Globe} count={online.length} lastUpdated={lastUpdated(online)} onAdd={() => setEditing({ kind: 'online', item: null })}>
        {online.length === 0 ? (
          <EmptyHint>Add your LinkedIn, GitHub, or portfolio links.</EmptyHint>
        ) : (
          <div className="space-y-3">
            {online.map((op: any) => (
              <ItemRow key={op.id} onEdit={() => setEditing({ kind: 'online', item: op })} onDelete={() => opDelete.mutate(op.id)}>
                <div className="flex items-center gap-2">
                  <ExternalLink size={14} className="text-slate shrink-0" />
                  <div className="min-w-0">
                    <p className="font-medium text-sm text-charcoal">{PLATFORM_TYPES.find((t: any) => t.value === op.platform_type)?.label || op.platform_type}</p>
                    <a href={op.url} target="_blank" rel="noopener noreferrer" className="text-xs text-cobalt story-link truncate block max-w-xs">{op.display_name || op.url}</a>
                  </div>
                </div>
              </ItemRow>
            ))}
          </div>
        )}
      </SectionCard>

      <Modal isOpen={editing?.kind === 'activity'} onClose={close} title={editing?.item ? 'Edit activity' : 'Add activity'}>
        <ActivityForm defaultValues={editing?.item} loading={actCreate.isPending || actUpdate.isPending} onSubmit={d => (editing?.item ? actUpdate.mutate({ id: editing.item.id, data: d }) : actCreate.mutate(d))} />
      </Modal>
      <Modal isOpen={editing?.kind === 'work'} onClose={close} title={editing?.item ? 'Edit work experience' : 'Add work experience'} size="lg">
        <WorkExperienceForm defaultValues={editing?.item} loading={workCreate.isPending || workUpdate.isPending} onSubmit={d => (editing?.item ? workUpdate.mutate({ id: editing.item.id, data: d }) : workCreate.mutate(d))} />
      </Modal>
      <Modal isOpen={editing?.kind === 'competition'} onClose={close} title={editing?.item ? 'Edit competition' : 'Add competition'} size="lg">
        <CompetitionForm defaultValues={editing?.item} loading={compCreate.isPending || compUpdate.isPending} onSubmit={d => (editing?.item ? compUpdate.mutate({ id: editing.item.id, data: d }) : compCreate.mutate(d))} />
      </Modal>
      <Modal isOpen={editing?.kind === 'portfolio'} onClose={close} title={editing?.item ? 'Edit portfolio item' : 'Add portfolio item'}>
        <PortfolioItemForm defaultValues={editing?.item} loading={pfCreate.isPending || pfUpdate.isPending} onSubmit={d => (editing?.item ? pfUpdate.mutate({ id: editing.item.id, data: d }) : pfCreate.mutate(d))} />
      </Modal>
      <Modal isOpen={editing?.kind === 'online'} onClose={close} title={editing?.item ? 'Edit link' : 'Add link'}>
        <OnlinePresenceForm defaultValues={editing?.item} loading={opCreate.isPending || opUpdate.isPending} onSubmit={d => (editing?.item ? opUpdate.mutate({ id: editing.item.id, data: d }) : opCreate.mutate(d))} />
      </Modal>
    </div>
  )
}
